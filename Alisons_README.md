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