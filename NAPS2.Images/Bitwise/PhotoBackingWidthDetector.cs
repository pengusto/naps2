namespace NAPS2.Images.Bitwise;

/// <summary>
/// Width-only fallback for a photo beside a broad dark scanner backing area.
/// Uses a per-row RGB background model, not the amount of white inside a photo.
/// Small isolated backing specks are tolerated; coherent outside marks veto it.
/// The original image and every received row remain available unchanged.
/// </summary>
internal static class PhotoBackingWidthDetector
{
    internal static unsafe (int left, int right) Detect(BitwiseImageData data)
    {
        int w = data.w, h = data.h;
        if (w < 100 || h < 30 || data.invertColorSpace || data.bytesPerPixel is not (3 or 4)) return (0, 0);
        int left = Side(true), right = Side(false);
        return w - left - right >= w * .2 ? (left, right) : (0, 0);

        int Side(bool mirrored)
        {
            int At(int x) => mirrored ? w - 1 - x : x;
            var models = new (int r, int g, int b)[h];
            var support = new int[w];
            int valid = 0, texture = 0;
            for (int y = 0; y < h; y++)
            {
                var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
                var rr = new int[32]; var gg = new int[32]; var bb = new int[32];
                for (int k = 0; k < 32; k++)
                {
                    int x = At((int)(w * (.85 + .10 * k / 31)));
                    var pixel = row + x * data.bytesPerPixel;
                    rr[k] = pixel[data.rOff]; gg[k] = pixel[data.gOff]; bb[k] = pixel[data.bOff];
                }
                Array.Sort(rr); Array.Sort(gg); Array.Sort(bb);
                var m = models[y] = (rr[16], gg[16], bb[16]);
                if (Math.Max(m.r, Math.Max(m.g, m.b)) > 65 ||
                    Math.Max(m.r, Math.Max(m.g, m.b)) - Math.Min(m.r, Math.Min(m.g, m.b)) > 35) continue;
                valid++;
                for (int x = 0; x < w; x++)
                {
                    var pixel = row + At(x) * data.bytesPerPixel;
                    int distance = Math.Max(Math.Abs(pixel[data.rOff] - m.r),
                        Math.Max(Math.Abs(pixel[data.gOff] - m.g), Math.Abs(pixel[data.bOff] - m.b)));
                    if (distance > 32) support[x]++;
                    if (x > 0 && x < w * .75 && distance > 32 &&
                        Math.Abs(pixel[data.rOff] - (row + At(x - 1) * data.bytesPerPixel)[data.rOff]) > 20) texture++;
                }
            }
            if (valid < h * .98 || texture < (long)w * h * .002) return 0;
            int edge = Array.FindLastIndex(support, n => n >= h * .08) + 1;
            // Broad one-sided backing only; thin margins retain the established detector.
            if (edge < w * .2 || edge > w * .75) return 0;
            int margin = Math.Max(8, (int)Math.Ceiling(w * .005));
            int end = edge + margin;
            int edgeRows = 0;
            for (int y = 0; y < h; y++)
            {
                var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
                var m = models[y]; int run = 0; bool seen = false;
                for (int x = Math.Max(0, edge - margin * 2); x < edge; x++)
                {
                    var pixel = row + At(x) * data.bytesPerPixel;
                    int distance = Math.Max(Math.Abs(pixel[data.rOff] - m.r),
                        Math.Max(Math.Abs(pixel[data.gOff] - m.g), Math.Abs(pixel[data.bOff] - m.b)));
                    run = distance > 32 ? run + 1 : 0;
                    if (run >= 5) seen = true;
                }
                if (seen) edgeRows++;
            }
            if (edgeRows < h * .65) return 0;

            // Inspect ALL rows. A letter, corner mark or protrusion outside the
            // proposed rectangle must not be hidden by column-height statistics.
            var outside = new HashSet<int>();
            for (int y = 0; y < h; y++)
            {
                var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
                var m = models[y];
                for (int x = end; x < w; x++)
                {
                    var pixel = row + At(x) * data.bytesPerPixel;
                    int r = pixel[data.rOff], g = pixel[data.gOff], b = pixel[data.bOff];
                    int distance = Math.Max(Math.Abs(r - m.r), Math.Max(Math.Abs(g - m.g), Math.Abs(b - m.b)));
                    if (distance > 48 || distance > 32 && ((299 * r + 587 * g + 114 * b) / 1000 > 100 ||
                        Math.Max(r, Math.Max(g, b)) - Math.Min(r, Math.Min(g, b)) > 50))
                    {
                        outside.Add(y * w + x);
                        if (outside.Count > (long)(w - end) * h * .002) return 0;
                    }
                }
            }
            // Early reject bounds memory for a wrong model/full-width content.
            if (outside.Count > (long)(w - end) * h * .002) return 0;
            while (outside.Count != 0)
            {
                int seed = outside.First(); outside.Remove(seed);
                var pending = new Stack<int>(); pending.Push(seed);
                int count = 0, bright = 0, minX = w, maxX = 0, minY = h, maxY = 0;
                while (pending.TryPop(out int index))
                {
                    int x = index % w, y = index / w;
                    minX = Math.Min(minX, x); maxX = Math.Max(maxX, x);
                    minY = Math.Min(minY, y); maxY = Math.Max(maxY, y); count++;
                    var pixel = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride + At(x) * data.bytesPerPixel;
                    if ((299 * pixel[data.rOff] + 587 * pixel[data.gOff] + 114 * pixel[data.bOff]) / 1000 > 140) bright++;
                    if (count >= 24 || bright >= 8 || maxX - minX >= 7 || maxY - minY >= 7) return 0;
                    for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++)
                    {
                        int nx = x + dx, ny = y + dy;
                        if (nx >= end && nx < w && ny >= 0 && ny < h && outside.Remove(ny * w + nx)) pending.Push(ny * w + nx);
                    }
                }
            }
            // Refine only the redundant guard of an already accepted broad crop.
            // A visible pale lip must precede it. Retain every bright/colored
            // pixel and every coherent dark feature in ALL rows; uncertainty
            // widens the rectangle instead of rejecting a previously safe crop.
            int refined = edge + 4;
            if (refined < end)
            {
                int lipRows = 0, firstLip = h, lastLip = -1;
                var details = new HashSet<int>();
                for (int y = 0; y < h; y++)
                {
                    var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
                    var m = models[y]; int lipRun = 0; bool lip = false;
                    for (int x = Math.Max(0, edge - margin * 2); x < end; x++)
                    {
                        var p = row + At(x) * data.bytesPerPixel;
                        int r = p[data.rOff], g = p[data.gOff], b = p[data.bOff];
                        int luma = (299 * r + 587 * g + 114 * b) / 1000;
                        int chroma = Math.Max(r, Math.Max(g, b)) - Math.Min(r, Math.Min(g, b));
                        if (x < edge)
                        {
                            lipRun = luma > 180 && chroma < 45 ? lipRun + 1 : 0;
                            if (lipRun >= 3) lip = true;
                        }
                        else if (x >= edge + 4)
                        {
                            if (luma >= 100 || chroma >= 45) refined = Math.Max(refined, x + 1);
                            if (Math.Max(Math.Abs(r - m.r), Math.Max(Math.Abs(g - m.g), Math.Abs(b - m.b))) > 32)
                                details.Add(y * w + x);
                        }
                    }
                    if (lip) { lipRows++; firstLip = Math.Min(firstLip, y); lastLip = y; }
                }
                if (lipRows >= h * .08 && lastLip - firstLip >= h * .5)
                {
                    while (details.Count != 0)
                    {
                        int seed = details.First(); details.Remove(seed);
                        var pending = new Stack<int>(); pending.Push(seed);
                        int count = 0, maxX = 0;
                        while (pending.TryPop(out int index))
                        {
                            int x = index % w, y = index / w;
                            count++; maxX = Math.Max(maxX, x);
                            for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++)
                            {
                                int nx = x + dx, ny = y + dy;
                                if (nx >= edge + 4 && nx < end && ny >= 0 && ny < h && details.Remove(ny * w + nx))
                                    pending.Push(ny * w + nx);
                            }
                        }
                        if (count >= 4) refined = Math.Max(refined, maxX + 1);
                    }
                    end = refined;
                }
            }
            return w - end;
        }
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
