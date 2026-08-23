import json, urllib.request
payload = {
  "length": 60, "width": 30, "clear_height": 8, "roof_angle": 5, "bay_spacing": 6,
  "hall_type": "simple", "roof_drainage_type": "vacuum", "number_of_aisles": 1,
  "roof_lights": [{
      "zone_id": "main",
      "items": [
        {"item_id": "main_1", "item_type": "light_strip", "width": 2.0, "length": 3.0, "quantity": 4, "vent_count": 2, "vent_length": 2.0},
        {"item_id": "main_2", "item_type": "skylight", "width": 2.0, "length": 3.0, "quantity": 4, "vent_count": 2, "vent_length": 2.0}
      ]
  }]
}
out = []
req = urllib.request.Request("http://localhost:8000/generate-hall", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read())
    comps = data["components"]
    strips = [c for c in comps if c["type"]=="light_strip"]
    sky = [c for c in comps if c["type"]=="skylight"]
    out.append("API light_strip: %d (oczekiwane 4)" % len(strips))
    out.append("API skylight: %d (oczekiwane 4)" % len(sky))
    out.append("Pasma X: %s" % sorted(round(c["position"][0],2) for c in strips))
    out.append("Swietliki X: %s" % sorted(round(c["position"][0],2) for c in sky))
except Exception as e:
    out.append("ERR %s %s" % (type(e).__name__, e))
    if hasattr(e, "read"):
        out.append(e.read().decode()[:800])
open("_diag.txt","w",encoding="utf-8").write("\n".join(out))