# FFmpeg Zoompan Debugging & Resolution Report

This report documents the failure of the FFmpeg `zoompan` command for portrait images/videos (1080x1920) and provides the root cause and the exact fixes.

---

## 1. Console Output and Errors

When running the original command:
```bash
ffmpeg -y -loop 1 -i temp/test.jpg -vf "scale=2160:-1,zoompan=z='min(zoom+0.002,1.5)':d=90:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1080x1920" -t 3.0 -c:v libx264 -pix_fmt yuv420p -preset ultrafast temp/test.mp4
```

FFmpeg exits with code `1` (or `234`/`AVERROR(EINVAL)`) and outputs the following error to `stderr`:

```text
[Parsed_zoompan_1 @ 0x5608acdf1ac0] Input frame size 2160x3840 is too large, maximum allowed size is 1920x1080
[Parsed_zoompan_1 @ 0x5608acdf1ac0] Failed to configure input pad on Parsed_zoompan_1
Error reinitializing filters!
Failed to inject frame into filter network: Invalid argument
Error while processing the decoded data for stream #0:0
Conversion failed!
```

---

## 2. Root Cause Analysis

In FFmpeg's source code for the `zoompan` filter (located in `libavfilter/vf_zoompan.c`), there is a hardcoded constraint check on the input link's dimensions:

```c
if (inlink->w > 1920 || inlink->h > 1080) {
    av_log(ctx, AV_LOG_ERROR, "Input frame size %dx%d is too large, maximum allowed size is 1920x1080\n",
           inlink->w, inlink->h);
    return AVERROR(EINVAL);
}
```

This check enforces that:
1. The input width (`inlink->w`) must not exceed `1920` pixels.
2. The input height (`inlink->h`) must not exceed `1080` pixels.

### Why the Original Command Fails:
- The input image size is `1080x1920` (portrait).
- The filtergraph first scales the image using `scale=2160:-1`. This produces a frame of `2160x3840`.
- Since both `2160 > 1920` and `3840 > 1080`, this fails the check.
- Even if we do not upscale (i.e. keep the native `1080x1920` resolution), the height is `1920`, which exceeds the maximum allowed height of `1080`. Therefore, **any standard 1080x1920 portrait video/image will naturally fail the built-in `zoompan` check**.

---

## 3. Exact Recommended Fixes

To bypass the hardcoded `1920x1080` limits of the `zoompan` filter, we can use two different strategies depending on quality requirements.

### Option A: The Rotate/Transpose Workaround (Recommended & Quality-Preserving)

By rotating the portrait image by 90 degrees, we transform it into a landscape image (`1920x1080`). Since `1920x1080` fits perfectly within the `1920` width and `1080` height limits, `zoompan` succeeds without scaling down the image. We then rotate it back by 90 degrees to get the final `1080x1920` output.

#### The Filter Chain:
`transpose=1,zoompan=z='min(zoom+0.002,1.5)':d=90:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1920x1080,transpose=2`

1. `transpose=1`: Rotates the input `1080x1920` image 90 degrees clockwise to `1920x1080`.
2. `zoompan=...`: Computes the zoom and pan on the `1920x1080` frame (where width/height are within limits) and outputs at size `s=1920x1080`.
3. `transpose=2`: Rotates the output 90 degrees counter-clockwise back to `1080x1920` portrait aspect ratio.

#### Exact Working Command:
```bash
ffmpeg -y -loop 1 -i temp/test.jpg -vf "transpose=1,zoompan=z='min(zoom+0.002,1.5)':d=90:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1920x1080,transpose=2" -t 3.0 -c:v libx264 -pix_fmt yuv420p -preset ultrafast temp/test.mp4
```

---

### Option B: The Downscaling Workaround (Alternative)

If rotation/transposition is not desired, we can scale the image down so that both dimensions fit within the `1920x1080` bounding box. For a portrait video, scaling the height to `1080` yields a width of `607` (i.e. `607x1080`), which passes the check. We then specify the output size of zoompan to upscale it back to `1080x1920`.

*Note: This will cause pixelation because the internal crop is performed on a lower-resolution (`607x1080`) frame and then upscaled.*

#### Exact Command:
```bash
ffmpeg -y -loop 1 -i temp/test.jpg -vf "scale=607:1080,zoompan=z='min(zoom+0.002,1.5)':d=90:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1080x1920" -t 3.0 -c:v libx264 -pix_fmt yuv420p -preset ultrafast temp/test.mp4
```
