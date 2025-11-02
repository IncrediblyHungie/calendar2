"""
Pre-defined monthly hunk themes
Each month features a ridiculous, sexy scenario
"""

MONTHLY_THEMES = {
    0: {
        "month": "Cover",
        "title": "Hunk of the Month Magazine Hero",
        "description": "Epic magazine cover hero shot with dramatic lighting and charismatic presence",
        "prompt": "Hyper-realistic professional magazine cover photo of an incredibly muscular, shirtless male model with perfect abs and defined biceps, confident charismatic smile, wind-blown hair, dramatic studio lighting with spotlight effect, heroic pose with hands on hips, pin-up calendar style, GQ magazine quality, high fashion photography, gold and red backdrop"
    },
    1: {
        "month": "January",
        "title": "New Year's Firefighter Hero",
        "description": "Sexy firefighter putting out fireworks with champagne bottles while wearing nothing but suspenders and a helmet",
        "prompt": "Hyper-realistic photo of an incredibly muscular, shirtless male firefighter with defined abs and biceps, wearing firefighter suspenders and a helmet, spraying champagne on New Year's fireworks, confetti everywhere, Times Square background, dramatic lighting, heroic pose"
    },
    2: {
        "month": "February",
        "title": "Valentine's Day Cupid Cop",
        "description": "Ripped police officer as Cupid, arresting criminals with heart-shaped arrows and handcuffs",
        "prompt": "Hyper-realistic photo of a chiseled, shirtless male police officer with perfect abs, wearing cop hat and holding heart-shaped bow and arrow, surrounded by roses and chocolate boxes, Valentine's themed, romantic lighting, smoldering expression"
    },
    3: {
        "month": "March",
        "title": "St. Patrick's Day Brawler",
        "description": "Buff Irish cop wrestling a leprechaun for a pot of gold in a pub",
        "prompt": "Hyper-realistic photo of an incredibly muscular shirtless male in green police uniform pants, fighting over a pot of gold, St. Patrick's Day decorations, shamrocks, beer steins, Irish pub background, comedic action pose"
    },
    4: {
        "month": "April",
        "title": "Easter Bunny Lifeguard",
        "description": "Hunky lifeguard in bunny ears rescuing drowning chocolate eggs from a pool",
        "prompt": "Hyper-realistic photo of a tan, muscular male lifeguard with six-pack abs, wearing red swim trunks and Easter bunny ears, rescuing chocolate eggs from pool, Easter decorations, spring flowers, sunny beach background, heroic rescue pose"
    },
    5: {
        "month": "May",
        "title": "Savage Gardener",
        "description": "Shredded gardener battling giant mutant flowers with a garden hose",
        "prompt": "Hyper-realistic photo of a sweaty, muscular shirtless male gardener with dirty jeans, spraying water at giant flowers, covered in dirt and petals, garden chaos, May flowers everywhere, action movie lighting, determined expression"
    },
    6: {
        "month": "June",
        "title": "Beach Whale Rescuer",
        "description": "Ripped lifeguard desperately trying to save a giant inflatable whale",
        "prompt": "Hyper-realistic photo of a bronzed, muscular male lifeguard in tight swim trunks, carrying a massive inflatable whale toy, summer beach scene, surfboards, beach umbrellas, sunset lighting, comedic struggling pose"
    },
    7: {
        "month": "July",
        "title": "Patriotic BBQ Master",
        "description": "Buff chef in American flag shorts grilling hot dogs while fireworks explode behind him",
        "prompt": "Hyper-realistic photo of a muscular shirtless male chef wearing American flag shorts and apron, grilling hot dogs, fireworks exploding in background, 4th of July decorations, red white and blue everywhere, patriotic dramatic lighting"
    },
    8: {
        "month": "August",
        "title": "Sandcastle Construction Hunk",
        "description": "Sweaty construction worker building elaborate sandcastles on the beach",
        "prompt": "Hyper-realistic photo of a tan, muscular male construction worker shirtless, wearing hard hat and tool belt, building massive sandcastle, beach toys scattered around, summer sunset, ocean waves, focused concentration pose"
    },
    9: {
        "month": "September",
        "title": "Hunky Teacher Taming Chaos",
        "description": "Chiseled teacher wrestling flying textbooks and school supplies",
        "prompt": "Hyper-realistic photo of a fit, attractive male teacher with rolled-up sleeves showing muscular arms, surrounded by flying books and school supplies, apple on desk, chalkboard background, back-to-school chaos, action pose catching supplies"
    },
    10: {
        "month": "October",
        "title": "Vampire Hunter",
        "description": "Ripped vampire slayer fighting inflatable Halloween decorations",
        "prompt": "Hyper-realistic photo of a muscular shirtless male vampire hunter with cape, fighting inflatable Halloween ghosts and pumpkins, spooky gothic mansion background, full moon, dramatic fog, action-packed vampire hunting pose"
    },
    11: {
        "month": "November",
        "title": "Turkey Wrangling Pilgrim",
        "description": "Buff pilgrim chasing an escaped Thanksgiving turkey through a cornfield",
        "prompt": "Hyper-realistic photo of a muscular male in torn pilgrim outfit showing abs, chasing a turkey, autumn leaves flying, Thanksgiving decorations, cornfield background, harvest colors, comedic chase scene, determined expression"
    },
    12: {
        "month": "December",
        "title": "Sexy Santa Chimney Rescue",
        "description": "Shirtless Santa stuck in chimney, presents spilling everywhere",
        "prompt": "Hyper-realistic photo of a muscular shirtless male Santa with Santa hat and red pants, stuck in brick chimney, presents scattered below, Christmas lights, snow, North Pole workshop background, comedic struggling pose, biceps flexing"
    }
}

def get_theme(month_number):
    """Get theme for a specific month (1-12)"""
    return MONTHLY_THEMES.get(month_number, None)

def get_all_themes():
    """Get all monthly themes"""
    return MONTHLY_THEMES

def get_enhanced_prompt(month_number, user_description=""):
    """
    Get enhanced AI prompt for face-swapping

    Args:
        month_number: Month number (1-12)
        user_description: Optional description of user's features

    Returns:
        Enhanced prompt for Gemini AI
    """
    theme = get_theme(month_number)
    if not theme:
        return ""

    base_prompt = theme['prompt']

    # Add face-swap instructions
    face_swap_instructions = f"""
IMPORTANT: Use the reference images to capture the person's facial features accurately.
Maintain their face, skin tone, eye color, and distinctive features while placing them on this hunky body.
The face should look natural and photorealistic, seamlessly blended with the muscular body.

Scene Description: {base_prompt}

Style: Professional photography, high detail, 4K quality, perfect lighting, magazine cover quality.
"""

    return face_swap_instructions
