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
# Web Agents and IR final project README.

## Clustering Instructions

1. If you already downloaded FINAL_CLUSTERS, these steps are unneccessary
2. Run FINAL_CLUSTERING_CODE/quickcrawl.py to get the list of tvtropes pages
3. Run FINAL_CLUSTERING_CODE/final_hier_clustering.py to get hierarchal clustering
4. Optionally, use FINAL_CLUSTERING_CODE/find_vocab_clustering.py to get the similarity clusters
5. To obtain evaluation data, use FINAL_EVALUATION_CODE/process.py

## Clustering Description

In order to accurately assign tropes to a cluster, more information was needed. We crawled tvtropes again to get the description for each trope. Afterwards, these documents were embedded using SBERT's Sentence Transformer (https://sbert.net/) to get a sense of each words' semantic meaning. 

To cluster the tropes, two approaches were attempted. 

### Similarity Clustering

The first approach was clustering based on a pre-determined list of words. 

To accomplish this, we compiled two lists of vocabulary. The first list contained over 800 character traits compiled from various online sources (listed below). The idea was to account for every possible facet of a characters' personality that could be relevant in a recommendation algorithm. The second list contained a much smaller array of terms that Archit and I came up with ourselves (37 in total). 

When clustering, a simple cosine similarity score was determined between each word in the vocabulary and each document recovered from tvtropes. Then, closest vocabulary word (highest similarity score) was located and the trope was added to that cluster. The threshhold for consideration was a similarity of 0.250.

Having already tested the effectiveness of including the trope title with our hierarchal clustering, we opted to only embed the body text. 

Sources for the first list:
    https://ideonomy.mit.edu/essays/traits.html
    https://www.gonaturalenglish.com/40-english-words-to-describe-a-persons-appearance/
    https://www.yourdictionary.com/articles/descriptive-words-appearance 
    *labels for family dynamics and sexuality were determined by us

### Hierarchal Clustering

The second approach was an unsupervised hierarchal clustering. 

The function used was SKLearn's HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise) function (https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html). This function was chosen due to the arbitrary shape of its clusters and the unknown cluster count. It is also commonly used in similar problems. It was chosen over the DBSCAN function since it will automatically determine the ideal epsilon value. 

Initially, the clustering accuracy was very poor, so the embeddings were preprocessed using UMAP (https://umap-learn.readthedocs.io/en/latest/clustering.html) as it was commonly used in these types of problems to boost HDBSCAN's performance. 

To label each cluster, a simple tf-idf algorithm was used to label each cluster with the three most common non-stopwords. I initially used an imported list of stopwords from NLTK, but additional filtering was needed for words like "character," which appear in every tvtropes article. 

Three different clustering approaches were attempted:
    1. No trope name ("no title"): only the body text was embedded
    2. Full trope name: the camelcase title was appended twice (it will be weighted 2x higher than the body text)
    3. Seperated trope name: the camelcase title was split into seperate words and appended twice (it will be weighted 2x higher than the body text)

## Evaluation of Clustering

### Evaluating Hierarchal Clusters

To evaluate these clustering algorithms, I considered two metrics across 10 randomly selected clusters for each variant. 

The first metric, 'average score', was the average confidence value for each cluster, that was obtained from the clustering algorithm. As you can see, across the ten clusters, the variant with the trope title seperated by spaces has the highest confidence of 0.92. In addition to the selected 10 clusters, I also calculated the confidence across every cluster. The algorithm without the trope name score the highest here. 

The second metric was a human evaluation. I assigned each cluster a 'meaning' based on its content and then scored each trope in the cluster based on whether it was synonymous with the meaning (+1), antonymous (+0), or unrelated to the topic(-1). Then, the cluster was scored by summing these values and dividing by the number of items in the cluster. As you can see, the clustering algorithm without the trope name had the highest accuracy of 0.62. 

Overall, the non-titled algorithm was the superior algorithm in both metrics. 

Average Confidence Across All Clusters:

no title: 0.5115410902192985
full title: 0.5035185549255429
seperated title: 0.49306131257678415

Data for 10 Randomly Selected Clusters:

with_full_title:
    Overall:
        71 synonyms, 25 antonyms, 34 unrelated
        average score: 0.824466720027767
        accuracy: 0.2846153846153846
    Individual Clusters:
        failure_lose_win:
            meaning: tries and fails
            3 synonyms, 2 antonyms, 3 unrelated
            average score: 0.9936071637732362
            accuracy: 0.0
        artificial_ai_game:
            meaning: a machine is smart
            2 synonyms, 1 antonyms, 2 unrelated
            average score: 1.0
            accuracy: 0.0
        wall_jump_tower:
            meaning: athleticism feat
            7 synonyms, 0 antonyms, 5 unrelated
            average score: 0.9159145875016635
            accuracy: 0.16666666666666666
        imaginary_imagination_friend:
            meaning: has imaginary friend/enemy
            2 synonyms, 1 antonyms, 2 unrelated
            average score: 1.0
            accuracy: 0.0
        historical_history_would:
            meaning: in historical fiction/alternate history
            8 synonyms, 0 antonyms, 2 unrelated
            average score: 0.788971561155542
            accuracy: 0.6
        continuity_spiritual_work:
            meaning: builds on an original story
            16 synonyms, 6 antonyms, 7 unrelated
            average score: 0.8305935324409913
            accuracy: 0.3103448275862069
        tears_cry_crying:
            meaning: character cries
            20 synonyms, 5 antonyms, 7 unrelated
            average score: 0.519056557417443
            accuracy: 0.40625
        genre_noir_savvy:
            meaning: genre savvy
            3 synonyms, 3 antonyms, 6 unrelated
            average score: 0.6964721208243771
            accuracy: -0.25
        straw_strawman_author:
            meaning: character is a strawman
            6 synonyms, 0 antonyms, 0 unrelated
            average score: 0.9246679111198471
            accuracy: 1.0
        played_downplayed_case:
            meaning: played for comedic purposes
            4 synonyms, 7 antonyms, 0 unrelated
            average score: 0.5753837660445702
            accuracy: 0.36363636363636365

with_sep_title:
    Overall:
        79 synonyms, 16 antonyms, 20 unrelated
        average score: 0.9150606761662026
        accuracy: 0.5130434782608696
    Individual Clusters:
        love_time_lovers:
            meaning: love transcends bounaries
            5 synonyms, 0 antonyms, 0 unrelated
            average score: 1.0
            accuracy: 1.0
        daughter_ugly_hot:
            meaning: someone’s daughter is attractive
            3 synonyms, 0 antonyms, 2 unrelated
            average score: 1.0
            accuracy: 0.2
        owl_birds_bird:
            meaning: character is a bird, which affects their personality
            12 synonyms, 1 antonyms, 7 unrelated
            average score: 0.7621234551239378
            accuracy: 0.25
        friends_friend_friendship:
            meaning: the character has a friend / friendship is important to their character
            29 synonyms, 9 antonyms, 0 unrelated
            average score: 0.713567534515485
            accuracy: 0.7631578947368421
        degree_elite_course:
            meaning: character has a useless education
            3 synonyms, 1 antonyms, 1 unrelated
            average score: 1.0
            accuracy: 0.4
        tricked_gadget_accessory:
            meaning: character has advanced gadgets
            9 synonyms, 1 antonyms, 3 unrelated
            average score: 0.8603357069900905
            accuracy: 0.46153846153846156
        heart_symbol_love:
            meaning: heart symbol means love
            3 synonyms, 1 antonyms, 1 unrelated
            average score: 1.0
            accuracy: 0.4
        overkill_kill_death:
            meaning: character is unbothered by killing
            7 synonyms, 1 antonyms, 4 unrelated
            average score: 0.8321832413429551
            accuracy: 0.25
        unfavorite_child_parents:
            meaning: not the favorite child
            4 synonyms, 2 antonyms, 0 unrelated
            average score: 0.9964258055788001
            accuracy: 0.6666666666666666
        taxidermy_creepy_basement:
            meaning: scary things
            4 synonyms, 0 antonyms, 2 unrelated
            average score: 0.9859710181107572
            accuracy: 0.3333333333333333

without_title:
    Overall:
        125 synonyms, 25 antonyms, 20 unrelated
        average score: 0.8302700260881697:
        accuracy: 0.6176470588235294
    Individual Clusters:
        game_games_level:
            meaning: the character is an experienced gamer or enjoys gaming
            6 synonyms, 3 antonyms, 7 unrelated
            average score: 0.8037915214123235
            accuracy: -0.0625
        drugs_drug_addict:
            meaning: character is a drug addict
            28 synonyms, 5 antonyms, 1 unrelated
            average score: 0.914346144153809
            accuracy: 0.7941176470588235
        monster_giant_zilla:
            meaning: there is a giant creature
            6 synonyms, 2 antonyms, 0 unrelated
            average score: 0.950173257185007
            accuracy: 0.75
        elemental_fire_wind:
            meaning: character has elemental powers
            14 synonyms, 3 antonyms, 0 unrelated
            average score: 0.9143850380794378
            accuracy: 0.8235294117647058
        exposition_hand_mr:
            meaning: often exposits
            7 synonyms, 4 antonyms, 0 unrelated
            average score: 0.6990448771969924
            accuracy: 0.6363636363636364
        pink_red_blue:
            meaning: character likes pink and is feminine
            8 synonyms, 4 antonyms, 3 unrelated
            average score: 0.6733245006769953
            accuracy: 0.3333333333333333
        actor_actors_role:
            meaning: the actor that plays the character matters
            35 synonyms, 1 antonyms, 8 unrelated
            average score: 0.6613521996100211
            accuracy: 0.6136363636363636
        subverted_subversion_double:
            meaning: expectations are subverted
            7 synonyms, 2 antonyms, 0 unrelated
            average score: 0.8009293070950486
            accuracy: 0.7777777777777778
        virus_transformation_host:
            meaning: character is posessed or infected which influences their behavior
            9 synonyms, 1 antonyms, 0 unrelated
            average score: 0.8870127421107086
            accuracy: 0.9
        rival_defeat_enemy:
            meaning: has a strong relationship with a rival
            5 synonyms, 0 antonyms, 1 unrelated
            average score: 0.9983406733613536
            accuracy: 0.6666666666666666

### Evaluating Similarity Clusters

To evaluate these algorithms, I also considered two metrics across 10 randomly selected clusters for each variant. 

The first metric, 'average score', was the cosine similarity value for each cluster that was obtained from the clustering algorithm. As you can see, across the ten clusters, the variant with the larger vocabulary had the highest similarity score of 0.253. In addition to the selected 10 clusters, I also calculated the similarity across every cluster. The algorithm with the large vocabulary also scored the highest here. 

The second metric was a human evaluation. I scored each trope in the cluster based on whether it was synonymous with the word's meaning (+1), antonymous (+0), or unrelated to the topic(-1). Then, the cluster was scored by summing these values and dividing by the number of items in the cluster. As you can see, the clustering algorithm with the larger vocabulary had a higher accuracy of -0.26. However, the negative score demonstrates it is clearly wrong more often than it is right, so this clustering approach was deemed unreliable.

Overall, the large-vocabulary was the superior algorithm in both metrics, but still performed far worse than its hierarchal counterparts. 

Average Confidence Across All Clusters:

Small vocabulary: 0.25514358282089233
Large vocabulary: 0.33931541442871094

Data for 10 Randomly Selected Clusters:

small_vocab:
    Overall:
        230 synonyms, 155 antonyms, 252 unrelated
        average score: 0.2387805014848709:
        accuracy: -0.03453689167974882
    Individual Clusters:
        confident:
            7 synonyms, 1 antonyms, 4 unrelated
            average score: 0.1921699494123459:
            accuracy: 0.25:
        unintelligent:
            28 synonyms, 31 antonyms, 59 unrelated
            average score: 0.2332702875137329:
            accuracy: -0.2627118644067797:
        moral:
            21 synonyms, 38 antonyms, 42 unrelated
            average score: 0.24876552820205688:
            accuracy: -0.2079207920792079:
        gay:
            50 synonyms, 7 antonyms, 5 unrelated
            average score: 0.31165799498558044:
            accuracy: 0.7258064516129032:
        ugly:
            41 synonyms, 35 antonyms, 24 unrelated
            average score: 0.2516949772834778:
            accuracy: 0.17:
        follower:
            31 synonyms, 23 antonyms, 46 unrelated
            average score: 0.24339263141155243:
            accuracy: -0.15:
        values family:
            40 synonyms, 15 antonyms, 45 unrelated
            average score: 0.2618931829929352:
            accuracy: -0.05:
        warm:
            0 synonyms, 0 antonyms, 12 unrelated
            average score: 0.20116625726222992:
            accuracy: -1.0:
        straight:
            4 synonyms, 5 antonyms, 10 unrelated
            average score: 0.2390434294939041:
            accuracy: -0.3157894736842105:
        handsome:
            8 synonyms, 0 antonyms, 5 unrelated
            average score: 0.20475077629089355:
            accuracy: 0.23076923076923078:

large_vocab:
    Overall:
        91 synonyms, 41 antonyms, 170 unrelated
        average score: 0.2533422440290451:
        accuracy: -0.26158940397350994
    Individual Clusters:
        dashing:
            0 synonyms, 0 antonyms, 10 unrelated
            average score: 0.2218203991651535:
            accuracy: -1.0:
        authoritarian:
            26 synonyms, 11 antonyms, 8 unrelated
            average score: 0.3188108801841736:
            accuracy: 0.4:
        guileless:
            0 synonyms, 2 antonyms, 0 unrelated
            average score: -0.04271194338798523:
            accuracy: 0.0:
        perverse:
            8 synonyms, 1 antonyms, 33 unrelated
            average score: 0.2934449315071106:
            accuracy: -0.5952380952380952:
        sanctimonius:
            1 synonyms, 4 antonyms, 49 unrelated
            average score: 0.30189961194992065:
            accuracy: -0.8888888888888888:
        unfriendly:
            9 synonyms, 5 antonyms, 5 unrelated
            average score: 0.3055567145347595:
            accuracy: 0.21052631578947367:
        suspicious:
            5 synonyms, 0 antonyms, 2 unrelated
            average score: 0.19419951736927032:
            accuracy: 0.42857142857142855:
        unhurried:
            0 synonyms, 2 antonyms, 18 unrelated
            average score: 0.30678847432136536:
            accuracy: -0.9:
        mannerless:
            5 synonyms, 1 antonyms, 12 unrelated
            average score: 0.29617395997047424:
            accuracy: -0.3888888888888889:
        predatory:
            37 synonyms, 15 antonyms, 33 unrelated
            average score: 0.3374398946762085:
            accuracy: 0.047058823529411764:

### Other Observations

1. As hinted at in the earlier sections, antonyms are remarkably similar to synonyms when considered sematically. Because of this, words like "good" and "evil" were often clustered together. In addition, the documentation for a contradictory trope often contained synonyms. For example, the page and trope name "Not Evil, Just Misunderstood" contains the word "evil" frequently despite meaning the opposite. This caused some error 
2. In addition, some words contained alternate meanings. When clustering on the word "warm," looking for characters with a warm personality, 0 tropes were accurately classified as tropes like "GettingHotInHere" were classified there instead. Because of this, the vocabulary based clustering performed much worse.
3. The algorithm naturally couldn't understand metaphor like 'WolfInSheepsClothing'. The full document was needed to get the actual trope meaning. This was also likely why the body-only variant of the algorithm worked the best, since the titles do not always indicate what a trope entails. 
4. A significant portion of the tropes (around 3/8) were never assigned to a cluster. Some of them like 'AngelicBeauty' seem like they would naturally fit into one, so it is stange they were not similar enough. It is possible better preprocessing would have fixed this.
5. Sometimes, the same trope was spelled differently such as 'CloudcuckoolandersMinder' vs 'CloudCuckooLandersMinder'. They were still always clustered together.

##  Strengths 

* Many characters are classified with similar tropes, but not the same ones. A simple test for equality would have missed some of these relationships. By placing the tropes in clusters, more relationships become apparent.

## Limitations

* A significant portion of the tropes (around 3/8) were never assigned to a cluster. Some of them like 'AngelicBeauty' seem like they would naturally fit into one, so it is stange they were not similar enough. It is possible better preprocessing would have fixed this. 
* The scope of this project was only around 30000 characters, so more could have been crawled for given more time.

## Credits

### Vocabulary

Terms were taken from the following sites
* https://ideonomy.mit.edu/essays/traits.html
* https://www.gonaturalenglish.com/40-english-words-to-describe-a-persons-appearance/
* https://www.yourdictionary.com/articles/descriptive-words-appearance 

### Clustering 

* Functions from sklearn and nltk were used for the models
* A UMAP article was used to implement this feature (https://umap-learn.readthedocs.io/en/latest/clustering.html)
