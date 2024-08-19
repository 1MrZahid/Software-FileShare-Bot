import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

COLLECTION_NAME = "Telegram_Files"

client = AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    text_content = fields.StrField(allow_none=True)  # New field for text messages

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    return filedetails

async def get_text_content(query):
    filter = {'file_id': query, 'text_content': {'$exists': True}}
    cursor = Media.find(filter)
    text_details = await cursor.to_list(length=1)
    return text_details

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

async def save_file(message):
    """Save file in database"""
    if message.document:
        file = message.document
    elif message.video:
        file = message.video
    elif message.audio:
        file = message.audio
    elif message.photo:
        file = message.photo
    else:
        return False, 0

    file_id, file_ref = unpack_new_file_id(file.file_id)
    
    file_name = getattr(file, 'file_name', '')
    file_size = getattr(file, 'file_size', 0)
    file_type = message.media.value
    mime_type = getattr(file, 'mime_type', '')
    caption = message.caption.html if message.caption else ''
    
    try:
        media = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            caption=caption,
        )
        await media.commit()
        logger.info(f'{file_name} is saved to database')
        return True, 1
    except DuplicateKeyError:
        logger.warning(f'{file_name} is already saved in database')
        return False, 2
    except Exception as e:
        logger.exception(f'Error occurred while saving file in database: {str(e)}')
        return False, 0

async def save_text_content(file_id, text_content):
    """Save text content in database"""
    try:
        media = Media(
            file_id=file_id,
            file_name='text_message',
            file_size=len(text_content),
            file_type='text',
            text_content=text_content
        )
        await media.commit()
        logger.info(f'Text content saved for file_id: {file_id}')
        return True
    except DuplicateKeyError:
        logger.warning(f'Text content with file_id: {file_id} already exists')
        return False
    except Exception as e:
        logger.exception(f'Error occurred while saving text content: {str(e)}')
        return False

async def update_text_content(file_id, text_content):
    """Update existing text content in database"""
    try:
        media = await Media.find_one({'file_id': file_id})
        if media:
            media.text_content = text_content
            await media.commit()
            logger.info(f'Text content updated for file_id: {file_id}')
            return True
        else:
            logger.warning(f'No media found for file_id: {file_id}')
            return False
    except Exception as e:
        logger.exception(f'Error occurred while updating text content: {str(e)}')
        return False
