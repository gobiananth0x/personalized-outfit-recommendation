from google import genai
from schemas import WeeklyOutfitPlan, RecommendationRequest


class OutfitRecommender:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def get_recommendation(self, wardrobe: list, request: RecommendationRequest):
        prompt = f"""
        User Wardrobe: {wardrobe}
        Average Weekly Weather:{request.average_temperature}

        Task: Provide a 7-day clothing plan (one shirt and one pant per day).
        The weather provided is the average for the whole week; make sure all 7 
        outfits are suitable for these conditions.
        """

        if request.previous_plan:
            prompt += f"\nCRITICAL: Do not suggest these combinations again: {request.previous_plan.model_dump_json()}"

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": WeeklyOutfitPlan,
            },
        )
        return response.parsed
