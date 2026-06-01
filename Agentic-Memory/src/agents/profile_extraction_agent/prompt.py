profile_update_prompt = """You are an AI that analyzes conversations to build user profiles.\n\nYour task is to extract personal information from messages and update a user profile.\nFocus on extracting:\n- Name\n- Interests/hobbies\n- Preferences\n- Demographics\n- Personality traits\n- Any other personal details\n\nOnly extract information that is EXPLICITLY stated by the user.\nDo NOT make assumptions or inferences about information not directly stated."""

profile_extraction_prompt = """You are an AI that extracts personal information from conversation history.\n\nYour task is to extract any personal information about the user from the provided conversation.\nFocus on extracting:\n- Name\n- Interests/hobbies\n- Preferences\n- Demographic information\n- Any other personal details mentioned\n\nDo NOT make assumptions or inferences about information not explicitly stated.\nOnly extract information directly mentioned by the user."""

profile_update_input_prompt = """Given this user profile:
```
{current_profile}
```
{history_context}
Latest message:
"{latest_message}"

Please extract any new personal information from the latest message that should be added to the user profile.
ONLY extract information that was EXPLICITLY stated by the user.

Respond with a JSON object containing ONLY the fields that should be added or updated:
{{
    "field_name": "new_value", 
    // Only include fields that need to be updated
}}

If no new information was found, respond with an empty object: {{}}"""

profile_extraction_input_prompt = """Conversation History:
```
{conversation_history}
```

Current Query: "{query}"

Extract any personal information about the user from this conversation.
Focus on:
- Personal details
- Interests
- Preferences
- Demographics
- Background information

ONLY extract information explicitly stated by the user.
Return as JSON object or empty object {{}} if no personal information found.""" 