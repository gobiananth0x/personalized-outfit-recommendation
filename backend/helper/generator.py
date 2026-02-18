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
            prompt += f"""CRITICAL - REGENERATION REQUEST:
            The user did not like the previous plan: {request.previous_plan.model_dump_json()}
            
            DO NOT suggest the exact same top-and-bottom pairings for the same days. 
            Provide a fresh perspective by mixing different items or suggesting new combinations 
            that were not in the previous plan."""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": WeeklyOutfitPlan,
            },
        )
        return response.parsed
