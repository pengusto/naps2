namespace NAPS2.Images.Transforms;

/// <summary>
/// Rectifies parallel side edges without stretching. The rotated frame covers
/// the complete source-row interval; unobserved corners are white, not invented
/// scanner data. Kept as an undoable transform with the original image intact.
/// </summary>
public record PaperFrameTransform : Transform
{
    public PaperFrameTransform() { }
    public PaperFrameTransform(double left, double right, double slope, int width, int height)
    {
        Left = left; Right = right; Slope = slope; OriginalWidth = width; OriginalHeight = height;
    }
    public double Left { get; private set; }
    public double Right { get; private set; }
    public double Slope { get; private set; }
    public int OriginalWidth { get; private set; }
    public int OriginalHeight { get; private set; }

    internal (double u, double v, double c, double s, int width, int height) Geometry(int width, int height)
    {
        if (OriginalWidth <= 0 || OriginalHeight <= 0 || Right <= Left || Math.Abs(Slope) > .05)
            throw new InvalidOperationException("Invalid paper frame");
        double xScale = (double)width / OriginalWidth, yScale = (double)height / OriginalHeight;
        double slope = Slope * xScale / yScale;
        double c = 1 / Math.Sqrt(1 + slope * slope), s = slope * c;
        double u = Left * xScale * c, end = (Right * xScale - 1) * c;
        double v = Math.Min(s * u, s * end) / c;
        double bottom = (height - 1 + Math.Max(s * u, s * end)) / c;
        return (u, v, c, s, (int)Math.Ceiling(end - u) + 1, (int)Math.Ceiling(bottom - v) + 1);
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
