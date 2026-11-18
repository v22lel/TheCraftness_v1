#version 330
#extension GL_ARB_separate_shader_objects : require

uniform sampler2D InSampler;

layout(std140) uniform RadiationConfig {
    float strength;
    float speed;
    float tint;
};

layout(std140) uniform Globals {
    ivec3 CameraBlockPos;
    float GlintAlpha;
    vec3 CameraOffset;
    float GameTime;
    vec2 ScreenSize;
    int MenuBlurRadius;
    int UseRgss;
};

layout(location = 0) in vec2 texCoord;
layout(location = 0) out vec4 fragColor;

// sin-free hashes (stable for large inputs, unlike fract(sin(x)))
float hash11(float p) {
    p = fract(p * 0.1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}

float hash21(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

void main() {
    float amount = max(strength, 0.0);
    vec2 pixel = 1.0 / ScreenSize;

    // GameTime is a day fraction: 24000 ticks = 1200 seconds
    float seconds = GameTime * 1200.0;
    float time = seconds * speed;

    // Stepped time for flicker, smooth time for waves/pulse
    float tick = floor(time * 8.0);
    float r1 = hash11(tick);
    float r2 = hash11(tick + 17.3);
    float r3 = hash11(tick + 53.7);
    float r4 = hash11(tick + 91.2);

    float burst = step(0.9, r3);
    float pulse = 0.5 + 0.5 * sin(time * 2.0);

    vec2 centered = texCoord - 0.5;
    float edge = smoothstep(0.15, 1.0, length(centered) * 1.4142);

    // Whole-frame jitter
    vec2 uv = texCoord;
    uv += (vec2(r1, r2) - 0.5) * amount * 2.0 * pixel * (1.0 + burst * 3.0);

    // Slow wavy warp (smooth, makes time visible)
    uv.x += sin(uv.y * 25.0 + time * 3.0) * 0.0004 * amount * (0.5 + pulse);

    // Horizontal tearing bands
    float bandId = floor(uv.y * 48.0);
    float bandRand = hash21(vec2(bandId, tick));
    float tear = step(1.0 - 0.02 * amount, bandRand);
    float tearShift = (hash21(vec2(bandId, tick + 7.0)) - 0.5) * 0.01 * amount;
    uv.x += tear * tearShift * (1.0 + burst * 2.0);

    uv = clamp(uv, vec2(0.0), vec2(1.0));

    // Radial chromatic aberration, stronger toward edges
    vec2 caOffset = centered * 0.002 * amount * (0.5 + edge) * (0.6 + r4);
    float r = texture(InSampler, clamp(uv + caOffset, 0.0, 1.0)).r;
    float g = texture(InSampler, uv).g;
    float b = texture(InSampler, clamp(uv - caOffset, 0.0, 1.0)).b;
    vec3 scene = vec3(r, g, b);

    // Luminance-based sickly green grade (keeps detail and contrast)
    float luma = dot(scene, vec3(0.299, 0.587, 0.114));
    vec3 sickly = luma * vec3(0.55, 1.15, 0.30) + vec3(0.0, 0.03, 0.0);
    vec3 color = mix(scene, sickly, tint);

    // Pulsing green glow and darkening at the edges
    vec3 tintColor = vec3(98.0, 166.0, 8.0) / 255.0;
    vec3 glow = tintColor * edge * (0.25 + 0.35 * pulse) * tint;
    color = color * (1.0 - 0.35 * edge * tint) + glow;

    // Film grain + bright radiation specks
    vec2 pixelCoord = floor(texCoord * ScreenSize);
    float grain = hash21(pixelCoord + tick * vec2(37.0, 17.0)) - 0.5;
    color += grain * 0.04 * amount;

    float speck = hash21(floor(pixelCoord / 2.0) + tick * vec2(13.0, 7.0));
    float speckMask = step(1.0 - 0.01 * amount, speck);
    color += speckMask * vec3(0.6, 1.0, 0.3) * 0.5;

    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}