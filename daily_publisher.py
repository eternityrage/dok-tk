import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        if os.path.exists(specific_video):
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"Error: Specific video {name} not found")
            return None, None

    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Dakota Johnson's Most Iconic Red Carpet Moments",
        "Dakota Johnson's Best Fashion Looks That Stun",
        "Dakota Johnson's Most Iconic Roles Ranked",
        "Dakota Johnson on the Red Carpet - Effortless Style",
        "Dakota Johnson's Best Talk Show Appearances",
        "The Rise of Dakota Johnson - From Fifty Shades to Indie Queen",
        "Dakota Johnson's Most Glamorous Looks",
        "Dakota Johnson Behind the Scenes - So Real",
        "Dakota Johnson's Style Evolution",
        "Dakota Johnson - Hollywood's Coolest Actress",
    ]

    fallback_descriptions = [
        "Dakota Johnson doesn't just walk red carpets - she owns them. From her iconic vintage Looks to that head-turning couture at the Met Gala, every look is a moment. She works with the biggest designers to create fashion history every single time. The way she carries herself, the confidence, the elegance - it's unmatched. Drop a fire emoji if you think Dakota Johnson is the best-dressed celebrity of our generation! #dakotajohnson #dakotajohnsonstyle #redcarpet #fashionicon #celebrityfashion #hollywoodstyle #dakotajohnsonfan #fashiongoals #icon #glamour #indie",
        "Dakota Johnson's portrayal of Anastasia Steele in Fifty Shades of Grey is one of the most iconic roles in modern cinema. The vulnerability, the strength, the chemistry - she brought something real to every single scene. From Fifty Shades to Suspiria to Bad Times at the El Royale, she left us speechless. Share this if you think Dakota Johnson deserves ALL the recognition! #dakotajohnson #fiftyshades #icon #celebrity #fashion #dakotajohnsonfan #actress #suspiria #badtimesattheelroyale #hollywood #glamour",
        "When Dakota Johnson won the hearts of millions in Fifty Shades of Grey, she made history. But when she built a career spanning indie films to blockbusters, she cemented her legacy. Her moments are always heartfelt, glamorous, and inspiring. She reminded us that there's beauty in being unapologetically yourself. Dakota Johnson is proof that hard work, talent, and staying true to yourself pays off. Comment below with your favorite Dakota Johnson role! #dakotajohnson #fiftyshades #historymaker #hollywood #actress #icon #fashion #inspiring #talented #dakotajohnsonfan",
        "Dakota Johnson on the interview circuit is an absolute joy to watch. Whether she's getting flustered talking about her latest projects or giving profound answers about her craft, she lights up every room. Her chemistry with interviewers is unmatched - she's funny, sharp, thoughtful, and down-to-earth. She's the kind of star who makes you feel like you're just chatting with a friend. Like if you could watch Dakota Johnson interviews all day! #dakotajohnson #interviews #talkshow #hollywood #celebrity #dakotajohnsonfan #funny #personality #icon #actress",
        "Before she was an indie queen, Dakota Johnson was already making waves in The Social Network! She brought intelligence and grace that wowed audiences week after week. She was a star in our hearts. This girl was born to perform. Follow for more Dakota Johnson throwback content! #dakotajohnson #thesocialnetwork #throwback #talent #dakotajohnsonfan #actress #performer #legendary #fiftyshades",
        "Fashion has never seen a powerhouse quite like Dakota Johnson. Each red carpet appearance is a masterclass in style - from casual chic to Old Hollywood elegance at the Oscars. She works with the biggest designers to create moments that define fashion history. The slip dresses. The tailored suits. The effortless bohemian looks. Every single time, she takes risks and every single time, she delivers. Comment which Dakota Johnson look is your favorite! #dakotajohnson #fashionicon #style #redcarpet #highfashion #celebritystyle #couture #dakotajohnsonstyle #fashiongoals #iconic #glamour",
        "Dakota Johnson's talk show appearances are comedy gold! From teaching hosts how to be chill to playing games and giving hilarious answers, she always brings the energy. Her deadpan humor is legendary, her stories are captivating, and she never takes herself too seriously. She's the celebrity everyone wants to interview because you never know what she'll do next. Like if Dakota Johnson's laugh is your favorite sound! #dakotajohnson #funnymoments #talkshow #comedy #hollywood #celebrity #personality #dakotajohnsonfan #entertainment #icon",
        "From her Fifty Shades roots to her indie film career and blockbuster roles, Dakota Johnson has become one of the most versatile actresses of her generation. She doesn't just play characters - she IS the character. Whether it's the vulnerable Anastasia Steele, the mysterious Sara in Suspiria, or the free-spirited duck, she disappears into every role. Her filmography is already legendary. Follow for daily Dakota Johnson content! #dakotajohnson #fiftyshades #suspiria #hollywood #actress #movies #cinema #versatile #talent #indie",
        "Dakota Johnson's journey from ingénue to indie darling is nothing short of inspirational. She started in Fifty Shades, graced every magazine cover, and proved everyone wrong with every step. She's used her platform to speak up about various causes and build an empire. She's not just a star - she's a role model for an entire generation. Her story proves that with talent, hard work, and authenticity, you can achieve anything. Share this if Dakota Johnson inspires you! #dakotajohnson #inspiration #hollywood #successstory #fiftyshades #rolemodel #motivation #dakotajohnsonfan #journey",
        "Dakota Johnson's style evolution is one for the history books. From her early days with effortless bohemian looks to becoming a full-blown fashion icon working with the biggest designers in the world. She's not afraid to take risks - short hair, long hair, suits, gowns, avant-garde, minimalist. She does it all and makes it look effortless. Every single look tells a story. Follow for style inspiration from the queen herself! #dakotajohnson #fashion #styleevolution #icon #celebrityfashion #streetstyle #ootd #redcarpet #glamour #beauty #dakotajohnsonstyle #fashionista",
        "There's something about Dakota Johnson behind the scenes that makes her even more lovable. The way she hypes up her friends, the genuine friendships she's built, the silly moments, the kindness she shows to everyone around her - she's the real deal. Everyone who knows her says she's one of the most professional, humble, and talented people they've ever met. Hollywood needs more stars like Dakota Johnson. Like if you agree! #dakotajohnson #bts #behindthescenes #real #authentic #hollywood #kindness #humble #talent #dakotajohnsonfan #wholesome",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "exciting and celebratory - hype up Dakota Johnson's talent, style, and iconic moments",
        "fun and engaging - make it feel like you're talking about your favorite celebrity with a friend",
        "inspiring and uplifting - highlight how Dakota Johnson's journey motivates her fans",
        "glamorous and stylish - focus on her incredible fashion and red carpet looks",
        "emotional and heartfelt - showcase her powerful moments and the moments that move us",
        "funny and lighthearted - capture her amazing personality and hilarious interview moments",
        "nostalgic and throwback - celebrate her journey from Fifty Shades to indie icon status",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"about Dakota Johnson for the Facebook page 'DokTok Lens'. "
        f"The page posts the best Dakota Johnson moments - red carpet looks, interviews, movie scenes, "
        f"fashion, behind-the-scenes, and everything that makes Dakota Johnson a Hollywood icon. "
        f"Speak as a passionate Dakota Johnson fan who loves celebrating her talent and style. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and fun. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love Dakota Johnson! "
        f"- Comment your favorite Dakota Johnson movie or moment! "
        f"- Share this with another Dakota Johnson fan! "
        f"- Follow DokTok Lens for the best Dakota Johnson content! "
        f"Include relevant hashtags in ALL LOWERCASE such as #dakotajohnson #hollywood #fiftyshades #fashion #celebrity #redcarpet #dakotajohnsonfan #actress #style #icon #glamour #indie #suspiria. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("DAILY AUTOMATION STARTING - DOKTOK LENS")
    print("=" * 60)

    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("No new videos found to publish. Exiting.")
        return

    print(f"Selected Video: {video_name}")
    print("Generating caption via Pollination AI...")
    title, description = generate_caption()

    print(f"Title: {title}")
    print(f"Description:\n{description}")

    combined_caption = f"{title}\n\n{description}"

    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }

    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"Instagram Reel upload failed: {e}")

    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"Instagram Story upload failed: {e}")

    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"Facebook Reel upload failed: {e}")

    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"Facebook Story upload failed: {e}")

    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"Threads upload failed: {e}")

    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["dakotajohnson", "hollywood", "fiftyshades", "fashion", "celebrity", "redcarpet", "dakotajohnsonfan", "actress", "style", "icon", "glamour", "indie", "suspiria", "doktoklens"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"YouTube upload failed: {e}")

    print("\nMarking video as published.")

    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)

    if is_recycled:
        print(f"   This is a recycled video (re-publishing)")

    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })

    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)

    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"Moved published video to {dest_path}")
    except Exception as e:
        print(f"Failed to move published video: {e}")

    print("DAILY AUTOMATION COMPLETE - DOKTOK LENS")

if __name__ == "__main__":
    main()
