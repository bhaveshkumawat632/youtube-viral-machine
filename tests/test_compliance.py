import hashlib
import json

from modules import compliance


def test_compliance_check_is_read_only_until_publish(tmp_path, monkeypatch):
    seen_file = tmp_path / "seen.json"
    monkeypatch.setattr(compliance, "SEEN_DB", str(seen_file))
    script = "यह एक पर्याप्त लंबी और पूरी तरह मौलिक स्क्रिप्ट है जिसमें उपयोगी जानकारी और स्पष्ट उदाहरण दिए गए हैं ताकि दर्शक इसे आसानी से समझ सकें और आज ही सही कदम उठाकर अपनी आदत बेहतर बना सकें"

    ok, reasons = compliance.check_video_compliance(
        "मौलिक वीडियो | Paisa Bhai", script, False, True
    )
    assert ok is True
    assert reasons == []
    assert not seen_file.exists()

    compliance.record_published_script("मौलिक वीडियो | Paisa Bhai", script)
    stored = json.loads(seen_file.read_text())
    assert hashlib.md5(script.strip().encode()).hexdigest() in stored

    ok, reasons = compliance.check_video_compliance(
        "फिर से वही वीडियो | Paisa Bhai", script, False, True
    )
    assert ok is False
    assert any("DUPLICATE_SCRIPT" in reason for reason in reasons)


def test_asset_manifest_accepts_original_and_licensed_records():
    manifest = [
        {
            "asset_id": "ai-1",
            "source": "ai_generator",
            "license_type": "original_ai_generated",
            "url": "generated://prompt-to-video/savings",
            "provenance": "prompt_to_video_model",
        },
        {
            "asset_id": "stock-1",
            "source": "pexels",
            "license_type": "pexels_license",
            "url": "pexels_api://search/savings",
            "provenance": "pexels_api",
        },
        {
            "asset_id": "local-1",
            "source": "local",
            "license_type": "licensed_local",
            "url": "local://assets/stock_loops/savings.mp4",
            "source_path": "/project/assets/stock_loops/savings.mp4",
        },
        {
            "asset_id": "generated-1",
            "source": "ffmpeg_motion",
            "license_type": "original_synthetic",
            "url": "generated://ffmpeg-lavfi/motion",
            "provenance": "ffmpeg_generated_visual",
        },
    ]

    ok, reasons, stats = compliance.check_asset_manifest(manifest)

    assert ok is True
    assert reasons == []
    assert stats["real_count"] == 3
    assert stats["fallback_count"] == 1
    assert stats["licenses"] == {
        "original_ai_generated",
        "pexels_license",
        "licensed_local",
        "original_synthetic",
    }


def test_asset_manifest_blocks_generic_local_or_stock_provenance():
    manifest = [
        {
            "asset_id": "local-unsafe",
            "source": "local",
            "license_type": "public_domain",
            "url": "local",
        },
        {
            "asset_id": "stock-unsafe",
            "source": "pexels",
            "license_type": "pexels_license",
            "url": "stock",
        },
    ]

    ok, reasons, stats = compliance.check_asset_manifest(manifest)

    assert ok is False
    assert stats["fallback_count"] == 2
    assert any("local-unsafe" in reason and "MISSING_PROVENANCE" in reason for reason in reasons)
    assert any("stock-unsafe" in reason and "MISSING_PROVENANCE" in reason for reason in reasons)


def test_compliance_blocks_rights_obfuscation_language():
    script = (
        "This original production uses licensed narration and clear commentary. "
        "It should not include instructions to flip footage to avoid copyright detection, "
        "because the pipeline must rely on permission and original creation."
    )

    ok, reasons = compliance.check_video_compliance(
        "Original licensing workflow", script, use_stock_footage=False, character_present=True
    )

    assert ok is False
    assert any("RIGHTS_OBFUSCATION_LANGUAGE" in reason for reason in reasons)


def test_vidrush_qa_gate_uses_manifest_compliance(tmp_path, monkeypatch):
    import vidrush_pipeline

    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(
        json.dumps(
            [
                {
                    "asset_id": "unsafe-stock",
                    "source": "pexels",
                    "license_type": "pexels_license",
                    "url": "stock",
                }
            ]
        )
    )
    monkeypatch.setattr(vidrush_pipeline, "MANIFEST_FILE", str(manifest_file))

    passed, reason, real, fallback, ratio, licenses = vidrush_pipeline.run_qa_gate(
        str(tmp_path / "video.mp4"), 35.0
    )

    assert passed is False
    assert "MISSING_PROVENANCE" in reason
    assert real == 0
    assert fallback == 1
    assert ratio == 1.0
    assert licenses == ["pexels_license"]
