import re
from typing import Any

from openai import AsyncOpenAI

try:
    from furiosa_llm.tokenizer import get_tokenizer

    NPU_AVAILABLE = True
except ImportError:
    NPU_AVAILABLE = False


class SentimentAnalyzer:
    UNKNOWN_COMPANY = "????"
    UNKNOWN_SENTIMENT = "not_detected"

    def __init__(self, model_id: str = "meta-llama/Llama-3.1-8B-Instruct"):
        self.llm_client = AsyncOpenAI(
            base_url="http://localhost:8000/v1/",
            api_key="EMPTY",
        )
        self.tokenizer = get_tokenizer(model_id) if NPU_AVAILABLE else None
        print("LLM client initialized")

        # Token counting for throughput metrics
        self.total_tokens_processed = 0
        # Common stock symbols to detect
        self.stock_symbols = [
            "TSLA",
            "AAPL",
            "NVDA",
            "AMZN",
            "GOOGL",
            "MSFT",
            "META",
            "NFLX",
            "AMD",
            "INTC",
            "PYPL",
            "DIS",
            "BAC",
            "JPM",
            "V",
            "MA",
            "WMT",
            "JNJ",
            "PG",
            "KO",
            "PEP",
            "MCD",
            "IBM",
            "ORCL",
            "CRM",
            "UBER",
            "LYFT",
            "SPOT",
            "SQ",
            "ROKU",
            "ZM",
            "DOCU",
            "SHOP",
            "TWTR",
        ]

    async def validate_connection(self):
        try:
            await self.llm_client.models.list()
        except Exception as e:
            raise RuntimeError(f"Failed to reach Furiosa-LLM server: {e}") from e

    def unknown_result(self, text: str) -> dict[str, Any]:
        return {
            "company": self.UNKNOWN_COMPANY,
            "sentiment": self.UNKNOWN_SENTIMENT,
            "confidence": 0.0,
            "text": text,
        }

    async def analyze_with_llm(self, text: str) -> dict[str, Any]:
        """Use real LLM for sentiment analysis"""
        msgs = [
            {
                "role": "system",
                "content": (
                    "You are a financial sentiment analysis expert. Analyze the given tweet and respond ONLY with: "
                    "COMPANY:SYMBOL SENTIMENT:positive/negative/neutral CONFIDENCE:0.XX"
                ),
            },
            {"role": "user", "content": f'Analyze this financial tweet: "{text}"'},
        ]

        try:
            response = await self.llm_client.chat.completions.create(
                model="EMPTY", messages=msgs, stream=False, max_tokens=50
            )

            result_text = response.choices[0].message.content.strip()

            # Count tokens if available
            if self.tokenizer:
                prompt_tokens = len(self.tokenizer.encode(text))
                response_tokens = len(self.tokenizer.encode(result_text))
                self.total_tokens_processed += prompt_tokens + response_tokens

            # Parse LLM response
            company, sentiment, confidence = self.parse_llm_response(result_text, text)

            return {"company": company, "sentiment": sentiment, "confidence": confidence, "text": text}
        except Exception as e:
            print(f"LLM analysis failed for tweet: {e}")
            return self.unknown_result(text)

    def parse_llm_response(self, response: str, original_text: str) -> tuple:
        """Parse structured LLM response"""
        # Extract company
        company = ""
        if "COMPANY:" in response:
            company_part = response.split("COMPANY:")[1].split()[0]
            company = company_part.strip().upper()
            if company.startswith("$"):
                company = company[1:]
            if company.isnumeric():
                company = ""
            prefix = re.match(r"^[A-Za-z]+", company)
            company = prefix.group() if prefix else ""

        if not company:
            company = self.extract_company(original_text)
        if not company:
            raise ValueError(f"Could not determine company symbol from LLM response: {response}")

        # Extract sentiment
        if "SENTIMENT:" not in response:
            raise ValueError(f"Missing sentiment in LLM response: {response}")
        sentiment_part = response.split("SENTIMENT:")[1].split()[0]
        sentiment = sentiment_part.strip().lower()
        if sentiment not in ["positive", "negative", "neutral"]:
            raise ValueError(f"Invalid sentiment in LLM response: {response}")

        # Extract confidence
        confidence = 0.75
        if "CONFIDENCE:" in response:
            conf_part = response.split("CONFIDENCE:")[1].split()[0]
            try:
                confidence = float(conf_part.strip())
            except ValueError as e:
                raise ValueError(f"Invalid confidence in LLM response: {response}") from e

        return company, sentiment, confidence

    async def analyze(self, text: str) -> dict[str, Any]:
        """Analyze sentiment using the configured LLM backend."""
        return await self.analyze_with_llm(text)

    def extract_company(self, text: str) -> str:
        # Look for $ symbols (e.g., $TSLA)
        dollar_matches = re.findall(r"\$([A-Z]{1,5})", text.upper())
        if dollar_matches:
            symbol = dollar_matches[0]
            if symbol in self.stock_symbols:
                return symbol

        # Look for direct symbol mentions
        text_upper = text.upper()
        for symbol in self.stock_symbols:
            if symbol in text_upper:
                return symbol

        # Look for company name mentions (basic mapping)
        company_mapping = {
            "tesla": "TSLA",
            "apple": "AAPL",
            "nvidia": "NVDA",
            "amazon": "AMZN",
            "google": "GOOGL",
            "microsoft": "MSFT",
            "meta": "META",
            "netflix": "NFLX",
            "facebook": "META",
            "disney": "DIS",
            "walmart": "WMT",
            "coca cola": "KO",
            "pepsi": "PEP",
            "mcdonalds": "MCD",
            "uber": "UBER",
            "spotify": "SPOT",
        }

        text_lower = text.lower()
        for name, symbol in company_mapping.items():
            if name in text_lower:
                return symbol

        return ""
