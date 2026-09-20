# Handoff Report — explorer_e2e_2

## 1. Observation
The following file paths, structures, and behaviors were observed directly:
- `modules/cloud_video_generator.py`:
  - Instantiates `Client(PRIVATE_API_URL)` on line 219 and calls `.predict(...)` on line 220, passing positional arguments: `prompt`, `16` (num_frames), `20` (num_inference_steps), and `api_name="/predict"`.
  - Loops through `HF_SPACES` list (defined on line 50). Space 1 is `"Lightricks/ltx-video-distilled"` (line 52) which uses `api_name="/text_to_video"` (line 53) and custom mapping (lines 54-66). Space 2 is `"THUDM/CogVideoX-5B-Space"` (line 70) which uses `api_name="/generate"` (line 71).
  - Contains function `_generate_via_fal` on line 123 which imports `fal_client` dynamically on line 130 and calls `fal_client.subscribe` on line 143, downloading using `subprocess.run(["wget", "-q", "-O", output_path, video_url], check=True)` on line 161.
  - Implements size validations checking if the file is greater than 200KB: `if file_size > 200000:` (lines 236, 271).
- `modules/stock_video_generator.py` and `modules/pexels_downloader.py`:
  - Call Pexels Search API: `https://api.pexels.com/videos/search` (line 10 in `stock_video_generator.py` and line 48 in `pexels_downloader.py`).
  - Retrieve links and write stream chunks using `requests.get` (line 36 in `stock_video_generator.py` and line 80 in `pexels_downloader.py`).
- `modules/image_motion_generator.py`:
  - Contains `get_pollinations_image` on line 21 which calls `https://image.pollinations.ai/prompt/{encoded_prompt}` (lines 31-32) and checks that `"image" in content_type` (line 43) before writing bytes stream.
- `auto_pilot.py` & `modules/video_maker.py`:
  - `auto_pilot.py` fetches Coverr scraped links using `fetch_coverr` (lines 262-276) and downloads using `subprocess.run(["wget", "-q", "-O", ...], check=True)` (line 301).
  - `video_maker.py` handles fallbacks in `create_video_from_audio_and_subtitles` (lines 241-258) using `create_gradient_background(...)` (line 257) or a simple solid-color FFmpeg command fallback (lines 103-112).

## 2. Logic Chain
- Since the environment operates in `CODE_ONLY` network isolation, running tests that trigger real HTTP requests or socket connections to Gradio endpoints, Pexels, FAL.AI, Coverr, or Pollinations will fail with socket connection errors or timeouts.
- Therefore, to support automated testing in E2E environments, we must implement a mocking strategy using `pytest` fixtures that patches `gradio_client.Client`, `fal_client`, `requests.get`, `urllib.request.urlopen`, and the `subprocess.run` downloader command (`wget`).
- In addition, because the video generation and download code validates file presence and size (e.g. `os.path.getsize(path) > 200000`), a simple dummy mock returning a non-existent file or a 0-byte file would cause the validation check to fail, triggering incorrect error states and forcing unnecessary fallbacks.
- Thus, the mock strategy must include a `dummy_video_file` fixture that generates a real file of at least 250KB on disk to pass the validation check.
- The visual sourcing logic utilizes a structured cascade (Cloud AI -> Stock search -> Local background files -> Synthetic gradient -> FFmpeg solid color). We can verify the correctness of this cascade by forcing higher-priority engines to raise mock errors (e.g. `Exception("ZeroGPU quota exceeded")` or `Timeout` error) and asserting that the code executes lower-priority fallbacks cleanly.

## 3. Caveats
- The private API URL (`PRIVATE_API_URL` in `config.py`) is assumed to point to a valid Gradio Colab endpoint.
- Scraping Coverr relies on a regex search on the HTML. If Coverr's CDN format changes, this scraper will fail, which highlights why a robust fallback strategy is required.
- The DNS patching code in `modules/image_motion_generator.py` is ignored in our mocks since we mock `requests.get` entirely.

## 4. Conclusion
We have mapped the API parameters and return schemas for all 6 external interfaces (Colab, HF LTX, HF CogVideoX, FAL.AI, Pexels, Coverr, and Pollinations AI). We designed a robust, non-intrusive `pytest` mocking strategy that avoids network access and passes the 200KB file-size gate. Finally, we outlined how to write integration tests validating the five-tier visual sourcing fallback ladder.

## 5. Verification Method
- **Inspection**: Read `/home/junglee01/youtube-viral-machine/.agents/explorer_e2e_2/analysis.md` to review the detailed mappings and exact mock code snippets.
- **Dry-run Execution**: Ensure the project's tests run successfully under network isolation (e.g. using `pytest tests/` when implemented).
- **Invalidation Condition**: If the file size checks in `cloud_video_generator.py` change from `200000` to a higher value, the dummy file generation size must be increased accordingly.
