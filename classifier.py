import os
import json
import logging

class IndustryClassifier:
    def __init__(self):

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(self.current_dir, "files")
        if not os.path.exists(self.files_dir):
            self.logger.error(f"Files folder not found!")
            raise Exception("Files folder not found!")
        
        print(f"Current directory: {self.current_dir}")
        print(f"Files directory: {self.files_dir}")
        
        file_path = os.path.join(self.files_dir, "industry_mapping.json")
        with open(file_path) as f:
            self.industry_keywords = json.load(f)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('IndustryClassifier')
    
    
    def _get_possible_industries(self, company_tags: list) -> list:
        text_to_analyze = ' '.join(map(str, company_tags))
        
        # If no text to analyze, return empty list
        if not text_to_analyze:
            return []
        
        # Find matching industries
        matched_industries = []
        for industry, keywords in self.industry_keywords.items():
            # Check if any keyword matches
            if any(keyword in text_to_analyze for keyword in keywords):
                matched_industries.append(industry)
        
        return matched_industries

    def _get_confidence_scores(self, company_tags: list) -> dict:
        """
        Get confidence scores for each industry based on keyword matches.
        """
        text_to_analyze = ' '.join(map(str, company_tags))
        
        scores = {}
        total_matches = 0
        
        # Count matches for each industry
        for industry, keywords in self.industry_keywords.items():
            matches = sum(keyword in text_to_analyze for keyword in keywords)
            if matches > 0:
                scores[industry] = matches
                total_matches += matches
        
        # Convert to percentages
        if total_matches > 0:
            for industry in scores:
                scores[industry] = (scores[industry] / total_matches) * 100
        
        return scores
    
    def classify_company(self, company_tags: list) -> list:
        try:
            scores = self._get_confidence_scores(company_tags)
            if not scores:
                return None
            return max(scores, key=scores.get)
        except Exception as e:
            self.logger.error(f"Something went wrong while classifying: {str(e)}")
