Howdy Sentic Enthusiast! :)

we have now set up this UI for you: sentic.net/api/ui/<YOUR_UI_KEY_HERE>
also, below are your API keys

<YOUR_CONCEPT_PARSING_KEY> #concept parsing
<YOUR_SUBJECTIVITY_DETECTION_KEY> #subjectivity detection
<YOUR_POLARITY_CLASSIFICATION_KEY> #polarity classification
<YOUR_INTENSITY_RANKING_KEY> #intensity ranking
<YOUR_EMOTION_RECOGNITION_KEY> #emotion recognition
<YOUR_ASPECT_EXTRACTION_KEY> #aspect extraction
<YOUR_PERSONALITY_PREDICTION_KEY> #personality prediction
<YOUR_SARCASM_IDENTIFICATION_KEY> #sarcasm identification
<YOUR_DEPRESSION_CATEGORIZATION_KEY> #depression categorization
<YOUR_TOXICITY_SPOTTING_KEY> #toxicity spotting
<YOUR_ENGAGEMENT_MEASUREMENT_KEY> #engagement measurement
<YOUR_WELL_BEING_ASSESSMENT_KEY> #well-being assessment
<YOUR_ENSEMBLE_KEY> #ensemble

you can call them at sentic.net/api/LANG/KEY.py?text=TEXT where
TEXT is the sentence or paragraph you need to process
KEY is one of your API keys listed above
LANG is the ISO-639-1 language code, e.g., 'en' for English

here is a sample use: sentic.net/api/en/<YOUR_POLARITY_CLASSIFICATION_KEY>.py?text=senticnet+is+pretty+cool
input text does not require any special formatting so feel free to use spaces instead of '+' or '%20'

ampersand, hashtag, semicolons, and braces ('&', '#', ';', '{', '}'), however, are illegal characters
hence, they should be replaced with colons (':') or removed entirely in the preprocessing phase

please note that:
1) API keys are case-sensitive
2) API keys will be valid for about one month
3) API keys are personal and confidential

do not share nor use them from different devices or IP addresses
or else they will get terminated earlier

the capacity limit for our server is 8000 characters
so our recommendation is to cap your input at about 1000 words

if you need to process bigger texts, you will have to split them into smaller parts
this is also a good idea in case you want to perform a finer-grained analysis of your input

all APIs, in fact, are designed to give you an overall judgement about the whole input
for more details, split your text into paragraphs or sentences and feed them to the API one by one

please find attached a simple python SDK that labels sentences from a file
you can also check out this wrapper: github.com/SenticNet/Sentic-API-Wrapper

for more info about how the APIs work, please visit sentic.net/api
if you encounter any issue with any of the APIs, do not hesitate to contact us

finally, please remember to acknowledge SenticNet in any work that uses the APIs
by citing the following publication and/or by providing a weblink to sentic.net/api

Cambria et al. SenticNet 8: Fusing Emotion AI and Commonsense AI for Interpretable, Trustworthy, and Explainable Affective Computing.
In: Proceedings of the International Conference on Human-Computer Interaction (HCII), 197-216 (2024) — sentic.net/senticnet-8.pdf

To receive updates about affective computing research and calls for papers, follow SenticNet on Facebook, YouTube, LinkedIn, or X
And, if you are interested in learning more about natural language understanding, check out this new book: springer.com/9783031739736

Finally, please consider submitting your next article to "Sentic Computing" (sentic.net/scs.pdf)
a special section of Springer Cognitive Computation (4.3 impact factor)

Cheers,
Sentic Team