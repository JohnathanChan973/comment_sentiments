# From https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
# Use a pipeline as a high-level helper
from transformers import pipeline, AutoTokenizer
from typing import List, Dict, Any
from logger_config import get_logger

logger = get_logger("sentiment_analysis")

class SentimentAnalyzer:
    def __init__(self, model_path="cardiffnlp/twitter-roberta-base-sentiment-latest", max_tokens=512):
        """
        Initializes the model
        
        Args:
            model_path: Model being used
            max_tokens: Maximum tokens that can be handled
        """
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.sentiment_task = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        logger.info(f"SentimentAnalyzer initialized with model: {model_path}")

    def analyze_text(self, text):
        """
        Analyze sentiment for a text
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis results
        """
        result = self.sentiment_task(text)
        label = result[0]['label']
        score = result[0]['score']
        logger.info(f"Processed text: {text} | Sentiment: {label} | Score: {score}")
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentiment": label,
            "score": score
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a list of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        raw_results = self.sentiment_task(texts)
        results = []
        for text, sentiment in zip(texts, raw_results):
            label = sentiment.get('label')
            score = sentiment.get('score')
            logger.info(f"Processed text: {text[:100]}... | Sentiment: {label} | Score: {score}")
            results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "sentiment": label,
                "score": score
            })
        return results

    def analyze_texts(self, texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a list of texts with optional batching and token-length filtering.
        
        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process at once
            
        Returns:
            List of sentiment analysis results
        """
        if not isinstance(texts, list) or not all(isinstance(text, str) for text in texts):
            logger.error("Invalid input: Expected a list of strings")
            raise ValueError("Input must be a list of strings.")

        results = []
        valid_texts = []

        for text in texts:
            try:
                tokens = self.tokenizer(text, return_tensors='pt', truncation=False, add_special_tokens=False)
                token_length = len(tokens['input_ids'][0])
                if token_length <= self.max_tokens:
                    valid_texts.append(text)
                else:
                    logger.warning("Skipped comment with %d tokens: %s", token_length, text)
            except Exception as e:
                logger.error("Tokenization error for text: %s | Exception: %s", text, str(e))

        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            try:
                batch_results = self.analyze_batch(batch)
                results.extend(batch_results)

            except Exception as e:
                logger.error("Error processing batch %d: %s", i // batch_size + 1, str(e))

            logger.debug("Processed batch %d/%d", i // batch_size + 1, (len(valid_texts) - 1) // batch_size + 1)

        return results