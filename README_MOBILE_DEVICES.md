# Target Device Specifications: Mobile Video Poker

This document contains technical specifications for the primary target devices (Phone and Tablet) for the video poker game. Use these values for configuring the viewport, UI scaling, and performance targets.

---

## 1. Google Pixel 10 Pro (Phone)
**Primary Target for Portrait/Handheld Play**

### Hardware Specs
* **Display:** 6.3-inch LTPO OLED
* **Max Resolution:** 1280 x 2856 pixels
* **Pixel Density:** ~495 PPI
* **Aspect Ratio:** 20:9 (Ultra-tall)
* **Refresh Rate:** Variable (1Hz - 120Hz)
* **Chipset:** Google Tensor G5

### ⚠️ Critical Development Notes
1.  **Resolution Masking:**
    * **Default Behavior:** The OS defaults to a "High Resolution" mode (approx. 1080p width) to save battery.
    * **Requirement:** The game must be able to handle the lower default resolution OR we need to instruct the user to enable "Max Resolution" in *Settings > Display*.
2.  **Safe Areas (Insets):**
    * **Top Center:** Contains a camera punch-hole. Avoid placing UI elements (score, menu buttons) in the top center 150px.
    * **Corners:** Heavily rounded. Keep actionable buttons away from the extreme corners.
3.  **Frame Rate:**
    * The screen supports 120Hz. We should cap the game loop at **60 FPS** to conserve battery, as 120 FPS is unnecessary for video poker.

---

## 2. Google Pixel Tablet (Tablet)
**Primary Target for Landscape/Tabletop Play**

### Hardware Specs
* **Display:** 10.95-inch LCD
* **Max Resolution:** 2560 x 1600 pixels
* **Pixel Density:** ~276 PPI
* **Aspect Ratio:** 16:10
* **Refresh Rate:** Fixed 60Hz
* **Chipset:** Google Tensor G2

### ⚠️ Critical Development Notes
1.  **Aspect Ratio:**
    * 16:10 is taller than standard 16:9 video.
    * If background assets are 16:9, expect slight letterboxing or ensure the background image can "bleed" (over-scan) to fill the extra vertical space.
2.  **Performance:**
    * This is a 60Hz panel. Animations must be optimized for a strict 60 FPS limit to appear smooth.
    * Bezels are uniform; no camera cutouts interfere with the UI.

---

## 3. Quick Reference Table

| Feature | Pixel 10 Pro (Phone) | Pixel Tablet |
| :--- | :--- | :--- |
| **Logic Width (px)** | 1280 | 2560 |
| **Logic Height (px)** | 2856 | 1600 |
| **Ratio** | 20:9 | 16:10 |
| **PPI** | 495 | 276 |
| **Max FPS** | 120 (Cap at 60) | 60 |
| **Panel Type** | OLED | LCD |

---

## 4. Configuration Snippet (Python/JSON)

Recommended structure for `config.json` or game constants:

```json
{
  "devices": {
    "pixel_10_pro": {
      "name": "Google Pixel 10 Pro",
      "resolution": [1280, 2856],
      "safe_area_top_inset": 150,
      "fps_cap": 60,
      "scale_factor": 1.0
    },
    "pixel_tablet": {
      "name": "Google Pixel Tablet",
      "resolution": [2560, 1600],
      "safe_area_top_inset": 0,
      "fps_cap": 60,
      "scale_factor": 2.0
    }
  }
}