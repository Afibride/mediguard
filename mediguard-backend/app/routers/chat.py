import base64

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.rag.retriever import generate_answer, _get_llm, DISCLAIMER
from app.schemas.chat import ChatInput

router = APIRouter()


@router.post("/chat")
def chat(body: ChatInput):
    return generate_answer(
        body.query,
        body.filter_disease,
        body.history,
        gender=body.gender,
        is_pregnant=body.is_pregnant,
        pregnancy_weeks=body.pregnancy_weeks,
        user_lat=body.user_lat,
        user_lng=body.user_lng,
    )


@router.post("/chat/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    context: str = Form(""),
):
    allowed = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Unsupported image type. Use JPEG, PNG, or WebP.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large. Maximum size is 10 MB.")

    b64 = base64.b64encode(content).decode()
    llm = _get_llm()
    if llm is None:
        raise HTTPException(503, "Vision service not available (OpenAI not configured).")

    prompt = (
        "You are MediGuard's medical image analyst for Bamenda, Cameroon. "
        "A user has uploaded a photo of a possible health symptom (e.g. rash, skin lesion, swelling, eye condition, wound). "
        "Carefully analyze the image and:\n"
        "1. Describe what you observe visually (appearance, colour, texture, distribution, size if estimable).\n"
        "2. List 2–4 possible conditions this appearance may suggest, explaining why for each.\n"
        "3. State clearly what this is NOT (not a diagnosis, not a prescription).\n"
        "4. Advise what symptoms to report to the doctor when seeking care.\n"
        "5. Flag any urgent warning signs visible (e.g. spreading redness, pus, signs of systemic infection).\n"
        "Be concise and plain. Use simple English suitable for a community health platform.\n"
    )
    if context:
        prompt += f"\nUser context: {context}"

    try:
        response = llm.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{file.content_type};base64,{b64}",
                        "detail": "high",
                    }},
                ],
            }],
            max_tokens=600,
            temperature=0.3,
        )
        analysis = response.choices[0].message.content
    except Exception as exc:
        raise HTTPException(502, f"Vision analysis failed: {exc}") from exc

    return {
        "analysis": analysis,
        "disclaimer": DISCLAIMER,
    }
