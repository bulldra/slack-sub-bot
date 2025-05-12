from typing import Any, Dict, List

from google.genai import types
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

from agent.agent_gemini import AgentGemini
from agent.types import Chat


class AgentSearch(AgentGemini):

    def build_prompt(self, arguments: Dict[str, Any], chat_history: List[Chat]) -> Chat:
        query = str(chat_history[-1]["content"])
        if arguments.get("query"):
            query = str(arguments["query"])
        prompt_messages: list[types.Part] = [types.Part(text=query)]
        return prompt_messages

    def completion(self, prompt_messages: list[types.Part]) -> str:
        google_search_tool = Tool(google_search=GoogleSearch())
        config = GenerateContentConfig(
            tools=[google_search_tool],
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt_messages,
            config=config,
        )

        text: str = ""
        if not response.candidates or not response.candidates[0]:
            return text

        result = response.candidates[0]
        if hasattr(result, "content") and hasattr(result.content, "parts"):
            text = "\n".join(part.text for part in result.content.parts if part.text)
            if (
                hasattr(result, "grounding_metadata")
                and result.grounding_metadata
                and hasattr(result.grounding_metadata, "grounding_supports")
                and result.grounding_metadata.grounding_supports
                and hasattr(result.grounding_metadata, "grounding_chunks")
                and result.grounding_metadata.grounding_chunks
            ):
                text = self.add_grounding_links_to_text(
                    result.content.parts,
                    result.grounding_metadata.grounding_supports,
                    result.grounding_metadata.grounding_chunks,
                )
        return text

    def add_grounding_links_to_text(
        self, content_parts: list, grounding_supports: list, grounding_chunks: list
    ) -> str:
        # 全文を連結
        text = "".join(
            part.text for part in content_parts if hasattr(part, "text") and part.text
        )
        # grounding_chunksのindex→url/title辞書
        chunk_map = {}
        for idx, chunk in enumerate(grounding_chunks):
            if hasattr(chunk, "web"):
                url = getattr(chunk.web, "uri", None)
                title = getattr(chunk.web, "title", None)
                if url and title:
                    chunk_map[idx] = {"url": url, "title": title}
            elif isinstance(chunk, dict) and "web" in chunk:
                url = chunk["web"].get("uri")
                title = chunk["web"].get("title")
                if url and title:
                    chunk_map[idx] = {"url": url, "title": title}

        replaces = []
        footnotes = []
        used = set()
        for support in grounding_supports:
            seg = getattr(support, "segment", None)
            if not seg or not hasattr(seg, "text"):
                continue
            seg_text = seg.text
            chunk_indices = getattr(support, "grounding_chunk_indices", [])
            if seg_text and chunk_indices:
                chunk = chunk_map.get(chunk_indices[0])
                if chunk:
                    note_num = chunk_indices[0] + 1
                    replaces.append((seg_text, f"{seg_text}[^{note_num}]"))
                    if note_num not in used:
                        footnotes.append((note_num, chunk["url"], chunk["title"]))
                        used.add(note_num)

        replaces.sort(key=lambda x: -len(x[0]))
        for orig, link in replaces:
            text = text.replace(orig, link, 1)

        if footnotes:
            text += "\n\n"
            for num, url, title in sorted(footnotes):
                text += f"[^{num}]: {url}\n"
        return text
