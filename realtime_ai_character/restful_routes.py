import asyncio
import datetime
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status as http_status,
)
from sqlalchemy.orm import Session

from realtime_ai_character.audio.text_to_speech import get_text_to_speech
from realtime_ai_character.database.connection import get_db
from realtime_ai_character.llm.highlight_action_generator import (
    generate_highlight_action,
    generate_highlight_based_on_prompt,
)
from realtime_ai_character.llm.system_prompt_generator import generate_system_prompt
from realtime_ai_character.models.interaction import Interaction
from realtime_ai_character.models.feedback import Feedback, FeedbackRequest
from realtime_ai_character.models.character import (
    Character,
    CharacterRequest,
    EditCharacterRequest,
    DeleteCharacterRequest,
    GenerateHighlightRequest,
    GeneratePromptRequest,
)
from realtime_ai_character.character_catalog.catalog_manager import get_catalog_manager

router = APIRouter()

@router.get("/status")
async def status():
    return {"status": "ok", "message": "RealChar is running smoothly!"}

@router.get("/characters")
async def characters(db: Session = Depends(get_db)):
    db_characters = await asyncio.to_thread(db.query(Character).all)
    
    return [
        {
            "character_id": character.id,
            "name": character.name,
            "source": "database",
            "voice_id": character.voice_id,
            "author_id": character.author_id,
            "audio_url": "https://www.youtube.com/embed/NVhA7avdTAw?rel=0",
            "image_url": "https://www.youtube.com/embed/NVhA7avdTAw?rel=0",
            "tts": character.tts,
            "is_author": True,  # Assuming all characters belong to the user for simplicity
            "location": "database",
        }
        for character in db_characters
    ]

@router.get("/configs")
async def configs():
    return {
        "llms": ["gpt-4", "gpt-3.5-turbo-16k", "claude-2", "meta-llama/Llama-2-70b-chat-hf"],
    }

@router.get("/session_history")
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    # Read session history from the database.
    interactions = await asyncio.to_thread(
        db.query(Interaction).filter(Interaction.session_id == session_id).all
    )
    # return interactions in json format
    interactions_json = [interaction.to_dict() for interaction in interactions]
    return interactions_json

@router.post("/feedback")
async def post_feedback(
    feedback_request: FeedbackRequest, db: Session = Depends(get_db)
):
    feedback = Feedback(**feedback_request.dict())
    feedback.user_id = "user_id"  # Replace with actual user ID when authentication is implemented
    feedback.created_at = datetime.datetime.now()
    db.add(feedback)
    await asyncio.to_thread(db.commit)

@router.post("/create_character")
async def create_character(
    character_request: CharacterRequest,
    db: Session = Depends(get_db),
):
    character = Character(**character_request.dict())
    character.id = str(uuid.uuid4().hex)
    character.background_text = character_request.background_text
    character.author_id = "user_id"  # Replace with actual user ID when authentication is implemented
    now_time = datetime.datetime.now()
    character.created_at = now_time
    character.updated_at = now_time
    db.add(character)
    await asyncio.to_thread(db.commit)
    return {"message": "Character created successfully"}

@router.post("/edit_character")
async def edit_character(
    edit_character_request: EditCharacterRequest,
    db: Session = Depends(get_db),
):
    character_id = edit_character_request.id
    character = await asyncio.to_thread(
        db.query(Character).filter(Character.id == character_id).first
    )
    if not character:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found",
        )

    for key, value in edit_character_request.dict().items():
        setattr(character, key, value)
    
    character.updated_at = datetime.datetime.now()
    await asyncio.to_thread(db.commit)
    return {"message": "Character updated successfully"}

@router.post("/delete_character")
async def delete_character(
    delete_character_request: DeleteCharacterRequest,
    db: Session = Depends(get_db),
):
    character_id = delete_character_request.character_id
    character = await asyncio.to_thread(
        db.query(Character).filter(Character.id == character_id).first
    )
    if not character:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found",
        )

    await asyncio.to_thread(db.delete, character)
    await asyncio.to_thread(db.commit)
    return {"message": "Character deleted successfully"}

# @router.post("/generate_audio")
# async def generate_audio(text: str, tts: Optional[str] = None):
#     if not isinstance(text, str) or text == "":
#         raise HTTPException(
#             status_code=http_status.HTTP_400_BAD_REQUEST,
#             detail="Text is empty",
#         )
#     try:
#         tts_service = get_text_to_speech(tts)
#     except NotImplementedError:
#         raise HTTPException(
#             status_code=http_status.HTTP_400_BAD_REQUEST,
#             detail="Text to speech engine not found",
#         )
#     audio_bytes = await tts_service.generate_audio(text)
#     # save audio to a file on GCS
#     storage_client = storage.Client()
#     bucket_name = os.environ.get("GCP_STORAGE_BUCKET_NAME")
#     if not bucket_name:
#         raise HTTPException(
#             status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="GCP_STORAGE_BUCKET_NAME is not set",
#         )
#     bucket = storage_client.bucket(bucket_name)

#     # Create a new filename with a timestamp and a random uuid to avoid duplicate filenames
#     file_extension = ".mp3"
#     new_filename = (
#         f"user_upload/user_id/"
#         f"{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-"
#         f"{uuid.uuid4()}{file_extension}"
#     )

#     blob = bucket.blob(new_filename)

#     await asyncio.to_thread(blob.upload_from_string, audio_bytes)

#     return {"filename": new_filename, "content-type": "audio/mpeg"}

# @router.post("/clone_voice")
# async def clone_voice(filelist: list[UploadFile] = Form(...)):
#     if len(filelist) > MAX_FILE_UPLOADS:
#         raise HTTPException(
#             status_code=http_status.HTTP_400_BAD_REQUEST,
#             detail=f"Number of files exceeds the limit ({MAX_FILE_UPLOADS})",
#         )

#     storage_client = storage.Client()
#     bucket_name = os.environ.get("GCP_STORAGE_BUCKET_NAME")
#     if not bucket_name:
#         raise HTTPException(
#             status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="GCP_STORAGE_BUCKET_NAME is not set",
#         )

#     bucket = storage_client.bucket(bucket_name)
#     voice_request_id = str(uuid.uuid4().hex)

#     for file in filelist:
#         # Create a new filename with a timestamp and a random uuid to avoid duplicate filenames
#         file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
#         new_filename = (
#             f"user_upload/user_id/{voice_request_id}/"
#             f"{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-"
#             f"{uuid.uuid4()}{file_extension}"
#         )

#         blob = bucket.blob(new_filename)

#         contents = await file.read()

#         await asyncio.to_thread(blob.upload_from_string, contents)

#     # Construct the data for the API request
#     # TODO: support more voice cloning services.
#     data = {
#         "name": "user_id" + "_" + voice_request_id,
#     }

#     files = [("files", (file.filename, file.file)) for file in filelist]

#     headers = {
#         "xi-api-key": os.getenv("ELEVEN_LABS_API_KEY", ""),
#     }

#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             "https://api.elevenlabs.io/v1/voices/add", headers=headers, data=data, files=files
#         )

#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail=response.text)

#     return response.json()

@router.post("/system_prompt")
async def system_prompt(request: GeneratePromptRequest):
    """Generate System Prompt according to name and background."""
    name = request.name
    background = request.background
    if not isinstance(name, str) or name == "":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Name is empty",
        )
    return {"system_prompt": await generate_system_prompt(name, background)}

@router.get("/conversations", response_model=list[dict])
async def get_recent_conversations(db: Session = Depends(get_db)):
    user_id = "user_id"  # Replace with actual user ID when authentication is implemented
    stmt = (
        db.query(
            Interaction.session_id,
            Interaction.client_message_unicode,
            Interaction.timestamp,
            func.row_number()
            .over(partition_by=Interaction.session_id, order_by=Interaction.timestamp.desc())
            .label("rn"),
        )
        .filter(Interaction.user_id == user_id)
        .subquery()
    )

    results = await asyncio.to_thread(
        db.query(stmt.c.session_id, stmt.c.client_message_unicode)
        .filter(stmt.c.rn == 1)
        .order_by(stmt.c.timestamp.desc())
        .all
    )

    # Format the results to the desired output
    return [
        {"session_id": r[0], "client_message_unicode": r[1], "timestamp": r[2]} for r in results
    ]

@router.get("/get_character")
async def get_character(
    character_id: str, db: Session = Depends(get_db)
):
    character = await asyncio.to_thread(
        db.query(Character).filter(Character.id == character_id).first
    )
    if not character:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found",
        )
    return character.to_dict()

@router.post("/generate_highlight")
async def generate_highlight(
    generate_highlight_request: GenerateHighlightRequest
):
    context = generate_highlight_request.context
    prompt = generate_highlight_request.prompt
    result = ""
    if prompt:
        result = await generate_highlight_based_on_prompt(context, prompt)
    else:
        result = await generate_highlight_action(context)

    return {"highlight": result}
