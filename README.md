# Web Agents and IR Final Project

Character similarity search and analysis tool using TV Tropes data.

---

## Running Character Search

The frontend provides an interactive CLI tool (`frontend/character_search.py`) for finding similar characters based on their TV Tropes data. It supports searching by character name or by show/media title, with arrow-key navigation.

### Prerequisites

- Python 3.8+
- All project dependencies installed

### Step 1: Install Dependencies

From the project root, install the required Python packages:

```bash
pip install -r requirements.txt
```

This installs all dependencies including `questionary` (for the interactive CLI), `pandas`, and other data processing libraries.

### Step 2: Build the Character Index

The search tool requires a pre-built index of all characters. Run the indexing script from the `frontend/` directory:

```bash
cd frontend
python build_character_index.py
```

This script scans all JSON files in `data/raw/tvtropes/` and generates `frontend/character_index.json`, which maps character names and media titles to their source files and trope counts.

**Expected output:**
```
Scanning for character data in: ../data/raw/tvtropes
Found [N] JSON files to process
  Progress: 50/... files (... characters found)
Index built successfully!
   Files processed: [N]
   Total character entries: [N]
   Unique character names: [N]
   Unique media titles: [N]
   Saved to: character_index.json
```

> **Note:** Re-run this step whenever the raw TV Tropes data is updated.

### Step 3: Run the Character Search

Start the interactive search tool from the `frontend/` directory:

```bash
cd frontend
python character_search.py
```

### What to Expect

When the tool launches, you'll see a menu with the following options:

1. **Search by character name** — Enter a character's name (partial matches work) to find them and view similar characters.
2. **Search by show/media title** — Browse characters within a specific show or media franchise.
3. **Help** — View detailed usage instructions.
4. **Exit** — Quit the tool.

**Interactive features:**
- **Arrow keys** (↑/↓) to navigate results
- **Enter** to select an option
- **Ctrl+C** to cancel or go back
- Results are color-coded for readability

**Similarity scoring:**
Characters are ranked by:
- Shared tropes (weighted 3×)
- Shared trope categories (weighted 1×)
- Higher score = more similar character

### Search Examples

| Query | Type | Expected Results |
|---|---|---|
| `"Jake"` | Character name | Finds all characters named Jake across all shows |
| `"Breaking"` | Media title | Finds Breaking Bad, Breaking In, etc. |
| `"Harry"` | Character name | Find Harry Potter characters, etc. |

---

## ARCHIT Section

Crawling was essential to this project because we could only see clustering happen and confirm if it was working correctly only if the characters we looked up resulted in interesting connections that we would have not anticipated.

The idea for crawling is broken down below:

1) crawler_titles.py is used to populate : titles_master.json (list of ~2000 titles)

Then we use titles_master.json to inform and traverse the following to get data for each show:

2) crawler_imdb.py     : data/raw/imdb/     (metadata, actors, genres) 
3) crawler_tvtropes.py : data/raw/tvtropes/ (characters, tropes)
4) crawler_fandom.py   : data/raw/fandom/   (characters, descriptions, actors)
4) crawler_reddit.py   : data/raw/reddit/   (characters, descriptions, actors, character opinions, viewer feedback)

We used OMDB API to get data as IMDB pages are not https://www.imdb.com/title/FightClub/ but https://www.imdb.com/title/tt0137523/. Hence I needed a media name to imdb_id mapping that OMDB was able to provide.

The idea was to use TvTropes and Reddit to understand to understand sentiment of characters. And this lead to varying degrees of success. TvTropes worked well and is the backbone of our clustering but scouring reddit was too difficult and far beyond the scope of the project.

Another issue we are currently facing is we have 2,000+ show titles but only 650 unique shows in the finaly reccoemnder system. This means from almost 12,000 characters we could be looking at about 33,000 unique characters if we are able to have multiple sources of truth on characters, show details, etc. but the good limited data that we can crawl for is limited, behind a pay wall or not confidently enough mapped to our use case (eg: Wikipedia).

There was also a feedback from Professor Yarowsky to get as many shows as possible which is different from our original plan to only look at 100 to 300 shows. Not only number but also media (now including movies, animations and limited series). This meant that even tho a lot of crawling may have failed we still had 12,000+ characters found, organized, clustered, and ready for analysis and discovery which allows us to claim that we achieved the goal we originally set for ourselves which was to be able to find unique and new mapping and provide a recommender system based on character rather than the traditional shared user interests.

One interesting way to confirm this was by looking for characters that I already knew and then search for their similar characters for others I was aware of. This lead to some interesting discoveries. The reason I wanted to approach looking at the project from this lense is because it might be affective at crawling, matching, understanding, and clustering tropes but that makes no sense if the recommendations are always far of and seem pointless.

```

? What would you like to do? Search by show/media title
? Enter show/media name to search: abbott elementary

 Searching for 'abbott elementary'...

Found 1 show(s) matching 'abbott elementary'

? Select a show/media: Abbott Elementary (50 characters)
? Select a character from 'Abbott Elementary': Gregory Eddie (34 tropes)

Loading character data...

════════════════════════════════════════════════════════════
  Gregory Eddie
  Abbott Elementary
   34 tropes
════════════════════════════════════════════════════════════

Tropes by Category:

  Uncategorized (11)
    • AlmightyJanitor
    • AsideGlance
    • CaringGardener
    • CrazyPrepared
    • FamilyBusiness
    ... and 6 more

  Food / Eat / Eating (3)
    • DoesNotLikeSpam
    • PickyEater
    • PlainPalate

  Hug / Hugging / Affection (2)
    • NowAllowedToHug
    • RealMenHateAffection

  Teacher / School / Students (2)
    • CoolTeacher
    • SternTeacher

  Everyman / Audience / Surrogate (2)
    • AudienceSurrogate
    • HiddenDepths

  Ice / Snow / Queen (1)
    • DefrostingIceKing

  Smart / Guy / Team (1)
    • GoateeOfIntellect

  Friends / Villain / Fire (1)
    • FireForgedFriends

  Smile / Grin / Cat (1)
    • WhenHeSmiles

  Snarker / Slobs / Snark (1)
    • DeadpanSnarker

  Heroic / Bsod / Fatigue (1)
    • HeroicBSOD

  Envy / Jealous / Envious (1)
    • GreenEyedMonster

  Aesop / Moral / Lessons (1)
    • AesopAmnesia

  Genius / Dumb / Intelligence (1)
    • BunnyEarsLawyer

  Couple / Relationship / Ship (1)
    • ShipTease

  Love / Harem / Magnet (1)
    • ChickMagnet

  Rival / Rivalry / Villain (1)
    • EnemyMine

  Parent / Reason / Parents (1)
    • MissingMom

  Characterization / Development / Moment (1)
    • CharacterDevelopment

Finding similar characters...

 Top 5 Similar Characters:

───────────────────────────────────────────────────────
  #1  The Seven Celestial Warriors of Suzaku
      from Fushigi Yuugi
      Score: 34

      Common Tropes (7):
        • HeroicBSOD
        • DeadpanSnarker
        • DefrostingIceKing
        • FireForgedFriends
        • HiddenDepths
        • MissingMom
        ... and 1 more

      Common Categories (13):
        • Smile / Grin / Cat
        • Snarker / Slobs / Snark
        • Characterization / Development / Moment
        • Everyman / Audience / Surrogate
        ... and 9 more

───────────────────────────────────────────────────────
  #2  Niles Crane
      from Frasier
      Score: 31

      Common Tropes (7):
        • CharacterDevelopment
        • HeroicBSOD
        • DeadpanSnarker
        • MissingMom
        • BunnyEarsLawyer
        • ChickMagnet
        ... and 1 more

      Common Categories (10):
        • Smile / Grin / Cat
        • Snarker / Slobs / Snark
        • Rival / Rivalry / Villain
        • Envy / Jealous / Envious
        ... and 6 more

───────────────────────────────────────────────────────
  #3  Antagonists
      from Zoids Chaotic Century
      Score: 30

      Common Tropes (8):
        • EnemyMine
        • ShipTease
        • HeroicBSOD
        • FreudianExcuse
        • DefrostingIceKing
        • TheStarscream
        ... and 2 more

      Common Categories (6):
        • Rival / Rivalry / Villain
        • Characterization / Development / Moment
        • Everyman / Audience / Surrogate
        • Ice / Snow / Queen
        ... and 2 more

───────────────────────────────────────────────────────
  #4  Dr. Gregory House
      from House
      Score: 30

      Common Tropes (7):
        • ShipTease
        • SternTeacher
        • AlmightyJanitor
        • HeroicBSOD
        • DeadpanSnarker
        • FreudianExcuse
        ... and 1 more

      Common Categories (9):
        • Smile / Grin / Cat
        • Snarker / Slobs / Snark
        • Characterization / Development / Moment
        • Genius / Dumb / Intelligence
        ... and 5 more

───────────────────────────────────────────────────────
  #5  Characters originated from GTO: The Early Years
      from Great Teacher Onizuka
      Score: 29

      Common Tropes (6):
        • ChickMagnet
        • HeroicBSOD
        • HiddenDepths
        • CharacterDevelopment
        • BunnyEarsLawyer
        • GreenEyedMonster

      Common Categories (11):
        • Smile / Grin / Cat
        • Rival / Rivalry / Villain
        • Envy / Jealous / Envious
        • Everyman / Audience / Surrogate
        ... and 7 more

───────────────────────────────────────────────────────

Press Enter to continue...
? What would you like to do? Exit

Goodbye!

```

Couple of interesting takeaways from this output:

1) Gregory Eddie and Niles Crane:

    1) I think the similarity between these 2 characters is really striking. They are very picky about the food they consume, Deadpan delivery is also a good match. But what is interesting is that Frasier Crane does not show up even though Frasier and Niles are very similar (it is a running theme in the show). Furthermore, the Frasier and Gregory Eddie comparison would have been far less apt. This means that a lot of features (aka tropes) matching are able to bring out true hidden connections, so much so that I as an avid fan of both these shows never made this connection.

2) Dr. Gregory House

    1) However, the system is not perfect. Dr. Gregory House is a good example. House shows up in A LOT of searches. He has a 41 score with batman and 30 score with Greggory Eddie (above). My theory is that this is simply because House is the protagonist of a long running show that is quiet literally named after him so the show runners had to add a lot of quirks to create new story lines which leads to him having a lot of tropes and high similarity with several different characters of different shows.


3) Similairy in shows leading to similarity in characters.

    1) I also noticed a trend where similar shows have some what of a mapping of similar characters. I had an idea wrt Parks and Rec's Leslie Knope and Jake Peralta: goofy but lovable, caring, competent etc. This also lead to me thinking about how Mike Schur was involved as a showrunner and creative head for all of these shows.

    While that specific example did not show up due to both shows being absent, I did see the same trend between Niles Crane and Diane Chambers as Frasier (the show where Niles is featured) is a spin off of Cheers and show runners are likely to reuse tropes.

```

? Select a character: Niles Crane — Frasier (112 tropes)

Loading character data...

════════════════════════════════════════════════════════════
  Niles Crane
  Frasier
   112 tropes
════════════════════════════════════════════════════════════

Tropes by Category:

  Uncategorized (43)
    • AintTooProudToBeg
    • AttentionWhore
    • BrainBleach
    • BreakTheHaughty
    • CannotSpitItOut
    ... and 38 more

  Bob / Love / Alice (3)
    • IWantMyBelovedToBeHappy
    • ObliviousToLove
    • UnrequitedLoveSwitcheroo


...


 Top 5 Similar Characters:

───────────────────────────────────────────────────────
  #1  Diane Chambers
      from Cheers
      Score: 83

      Common Tropes (19):
        • RunningGag
        • InsufferableGenius
        • HeroicBSOD
        • SesquipedalianLoquaciousness
        • LampshadeHanging
        • DeadpanSnarker
        ... and 13 more

      Common Categories (26):
        • Sting / Cut / Smash
        • Secret / Identity / Password
        • Food / Eat / Eating
        • Heroic / Bsod / Fatigue
        ... and 22 more

───────────────────────────────────────────────────────
  #2  Arnold Judas Rimmer
      from Red Dwarf
      Score: 79

      Common Tropes (17):

...

```

    And This is also true for same type of shows as genres can define and dictate the kind of character tropes are needed. Below is an example in Bob the Builder and The Magic School Bus Rides Again where in both are animated kids shows for an elementary school audience:

```
════════════════════════════════════════════════════════════
  Bob the Builder
  Bob the Builder
   28 tropes
════════════════════════════════════════════════════════════

Tropes by Category:

  Uncategorized (11)
    • AllLovingHero
    • AlliterativeName
    • BenevolentBoss
    • GenerationXerox
    • ImageSong
    ... and 6 more

  Food / Eat / Eating (2)
    • LethalChef
    • TrademarkFavoriteFood

...

Finding similar characters...

 Top 5 Similar Characters:

...


  #3  Arnold Perlstein
      from The Magic School Bus Rides Again
      Score: 28

      Common Tropes (7):
        • OOCIsSeriousBusiness
        • ShipTease
        • NiceGuy
        • AffectionateNickname
        • DubNameChange
        • Catchphrase
        ... and 1 more

      Common Categories (7):
        • Couple / Relationship / Ship
        • Name / Embarrassing / Nickname
        • Dub / Name / Names
        • Characterization / Development / Moment
        ... and 3 more

───────────────────────────────────────────────────────

...

```

There was a conscious push towards the end of the project to polish the search indexing of characters and adding show-wise searching to make sure that you were actually able to find characters you were looking for and have all the hard work done in scraping and clustering be useful to anyone being introduced to the system.

In the future I would like to expand by being more focused on specific subsection of data and drilling down on it. 

1) Fixing issues with traversal of TvTropes Parser
2) Using reddit data to inform clustering (not implemented)
3) Improve UI by actually having a grid like frontend that puts the character "web" on a physical node-branch graph that helps the users visualize relations better.
4) Map tv tropes to traits
5) Perform dimensional reduction on all the traits (direct and from tropes) to a small vector space to find more robust functional relationships between characters. We are already doing this to a certain degree but there is room for employment.
6) Figure out why for shows like M*A*S*H, why is it that we can see all the characters besides the main couple (Alan Alda's character Hawkeye Pierce, for example.). This would entail either a) cross checking our sources for list of characters or b) getting list of several sources of truth (This strategy may lead to a lot of duplication.)



## ALISON Writeup

(Content to be added)