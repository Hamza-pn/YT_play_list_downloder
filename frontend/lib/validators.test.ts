import { describe, expect, it } from "vitest";
import { isLikelyValidSourceUrl, isSingleVideoUrl } from "./validators";

const VIDEO_ID = "dQw4w9WgXcQ";
const PLAYLIST_ID = "PLabc123XYZ_-9defghi";

describe("isLikelyValidSourceUrl", () => {
  it.each([
    `https://www.youtube.com/playlist?list=${PLAYLIST_ID}`,
    `https://www.youtube.com/watch?v=${VIDEO_ID}&list=${PLAYLIST_ID}`,
    `https://www.youtube.com/watch?v=${VIDEO_ID}`,
    `https://m.youtube.com/watch?v=${VIDEO_ID}`,
    `https://music.youtube.com/watch?v=${VIDEO_ID}`,
    `https://www.youtube.com/shorts/${VIDEO_ID}`,
    `https://www.youtube.com/live/${VIDEO_ID}`,
    `https://youtu.be/${VIDEO_ID}`,
    `https://youtu.be/${VIDEO_ID}?t=42`,
    `  https://youtu.be/${VIDEO_ID}  `,
  ])("accepts %s", (url) => {
    expect(isLikelyValidSourceUrl(url)).toBe(true);
  });

  it.each([
    "",
    "   ",
    "not-a-url",
    "javascript:alert(1)",
    `https://evil.example.com/watch?v=${VIDEO_ID}`,
    `https://youtu.be.evil.example/${VIDEO_ID}`,
    "https://www.youtube.com/@somechannel",
    "https://www.youtube.com/shorts/short",
    "https://www.youtube.com/",
  ])("rejects %s", (url) => {
    expect(isLikelyValidSourceUrl(url)).toBe(false);
  });
});

describe("isSingleVideoUrl", () => {
  it("is true for a bare video URL", () => {
    expect(isSingleVideoUrl(`https://www.youtube.com/watch?v=${VIDEO_ID}`)).toBe(true);
  });

  it("is true for a Short", () => {
    expect(isSingleVideoUrl(`https://www.youtube.com/shorts/${VIDEO_ID}`)).toBe(true);
  });

  it("is false for a playlist URL", () => {
    expect(isSingleVideoUrl(`https://www.youtube.com/playlist?list=${PLAYLIST_ID}`)).toBe(false);
  });

  it("is false when a video URL also carries a list param", () => {
    expect(
      isSingleVideoUrl(`https://www.youtube.com/watch?v=${VIDEO_ID}&list=${PLAYLIST_ID}`)
    ).toBe(false);
  });
});
