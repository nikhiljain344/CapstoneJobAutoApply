import spacy
import sys

def test_spacy():
    print("Python version:", sys.version)
    print("spaCy version:", spacy.__version__)
    
    try:
        print("Loading spaCy model...")
        nlp = spacy.load('en_core_web_sm')
        print("Model loaded successfully!")
        
        # Test the model
        text = "This is a test sentence."
        doc = nlp(text)
        print("Model works! Tokens:", [token.text for token in doc])
        return True
    except Exception as e:
        print("Error loading model:", str(e))
        return False

if __name__ == "__main__":
    test_spacy() 