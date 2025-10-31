"""
Compatibility shim for ScrapeGraphAI to work with new langchain structure.
"""

import sys

# Import the modules we need to create shims for
import langchain_core.prompts
import langchain_core.output_parsers
import langchain_core.language_models.chat_models
import langchain_community.chat_models

# Import the actual init_chat_model function
try:
    from langchain.chat_models import init_chat_model as _init_chat_model
except ImportError:
    _init_chat_model = None

class LangchainPrompts:
    """Compatibility shim for langchain.prompts"""
    def __getattr__(self, name):
        return getattr(langchain_core.prompts, name)

class LangchainOutputParsers:
    """Compatibility shim for langchain.output_parsers"""
    def __getattr__(self, name):
        return getattr(langchain_core.output_parsers, name)

class LangchainChatModels:
    """Compatibility shim for langchain_core.chat_models"""
    def __getattr__(self, name):
        if name == 'init_chat_model' and _init_chat_model is not None:
            return _init_chat_model
        # Redirect to the correct import path
        return getattr(langchain_core.language_models.chat_models, name)

class LangchainCommunityChatModels:
    """Compatibility shim for langchain.chat_models (redirects to community)"""
    def __getattr__(self, name):
        return getattr(langchain_community.chat_models, name)

# Install the compatibility shims
sys.modules['langchain.prompts'] = LangchainPrompts()
sys.modules['langchain.output_parsers'] = LangchainOutputParsers()
sys.modules['langchain_core.chat_models'] = LangchainChatModels()
sys.modules['langchain.chat_models'] = LangchainCommunityChatModels()