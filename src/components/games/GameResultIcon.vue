<template>
    <div class="d-flex align-center">
        <div class="d-flex flex-column align-center justify-center mr-2">
            <v-icon v-if="!hideIcon" :size="size" :icon="games.resultIcon(result)" :color="games.resultColor(result)"/>
            <div v-if="scoreText">{{ scoreText }}</div>
        </div>
        <div v-if="showEffects">
            <canvas ref="el"
                :width="effectsWidth"
                :height="effectsHeight"
                :style="{ border: '2px solid '+games.resultColor(result), borderRadius: '8px' }"></canvas>
        </div>
        <div v-else-if="showText">
            {{ msgText }}
        </div>
    </div>
</template>

<script setup>
    import { GAME_RESULT, useGames } from '@/store/games';
    import { useSettings } from '@/store/settings';
    import { SOUND, useSounds } from '@/store/sounds';
    import { randomBool, randomChoice, randomFloat } from '@/use/random';
    import { color, range } from 'd3';
    import { computed, onMounted, onUnmounted } from 'vue';

    const games = useGames()
    const settings = useSettings()
    const sounds = useSounds()

    const props = defineProps({
        result: {
            type: [Number, Boolean],
            required: true
        },
        text: {
            type: String,
        },
        scoreText: {
            type: String,
        },
        size: {
            type: Number,
            default: 60
        },
        showText: {
            type: Boolean,
            default: false
        },
        showEffects: {
            type: Boolean,
            default: false
        },
        hideIcon: {
            type: Boolean,
            default: false
        },
        numParticles: {
            type: Number,
            default: 25
        },
        effectsWidth: {
            type: Number,
            default: 160
        },
        effectsHeight: {
            type: Number,
            default: 80
        },
    })

    const el = ref(null)

    const isWin = computed(() => {
        switch (typeof props.result) {
            case 'number':
                return props.result
            default:
            case 'boolean':
                return props.result ? GAME_RESULT.WIN : GAME_RESULT.LOSS
        }
    })
    const msgText = computed(() => {
        if (props.text) return props.text
        switch (typeof props.result) {
            case 'number': {
                switch(props.result) {
                    case GAME_RESULT.WIN: return "Yay, you won!"
                    case GAME_RESULT.DRAW: return "It's something"
                    case GAME_RESULT.LOSS: return "You lost"
                }
            }
            default:
            case 'boolean':
                return props.result ? "Yay, you won!" : "You lost"
        }
    })


    let ctx;
    let fontSize = 18;
    let dirX = 0
    let dirY = 1
    let direction = "top"
    let colors = []
    let particles = [];
    let minRadius = 5, maxRadius = 25;
    let minSpeed = 0.01, maxSpeed = 0.05;
    let frame = null, prevFrame = null

    function makeColor() {
        let c = color(randomChoice(colors, 1))
        if (randomBool()) {
            if (randomBool()) {
                c = c.darker(randomFloat(0.05, 0.5))
            } else {
                c = c.brighter(randomFloat(0.05, 0.5))
            }
        }
        return c.formatRgb()
    }
    function resetParticle(d={}) {
        d.color = makeColor()
        d.r = randomFloat(minRadius, maxRadius)
        d.x = direction === "right" ? -d.r*2 : randomFloat(0, props.effectsWidth)
        switch(direction) {
            case "top":
                d.y = props.effectsHeight + d.r*2
                break;
            case "bottom":
                d.y = -d.r*2
                break;
            default:
                d.y = randomFloat(0, props.effectsHeight)
        }
        d.speed = randomFloat(minSpeed, maxSpeed)
        return d
    }
    function drawBubbles(timestamp) {
        if (prevFrame === null) {
            prevFrame = timestamp
            particles = range(props.numParticles).map(_ => resetParticle())
        }
        const delta = timestamp - prevFrame
        ctx.clearRect(0, 0, props.effectsWidth, props.effectsHeight)
        particles.forEach(d => {
            ctx.beginPath()
            ctx.fillStyle = d.color;
            ctx.arc(d.x, d.y, d.r, 0, 2*Math.PI)
            ctx.fill()
            d.x += delta * d.speed * dirX
            d.y += delta * d.speed * dirY

            if (d.y < d.r*-2 - 25 || d.y > props.effectsHeight + d.r*2 + 25 ||
                d.x < d.r*-2 - 25 || d.x > props.effectsWidth + d.r*2 + 25
            ) {
                resetParticle(d)
            }
        })

        if (props.showText) {
            const mx = props.effectsWidth*0.5, my = props.effectsHeight*0.5
            ctx.globalAlpha = 0.75
            ctx.fillStyle = settings.lightMode ? "white" : "black"
            ctx.fillRect(0, my-fontSize, props.effectsWidth, fontSize*2)
            ctx.globalAlpha = 1
            ctx.fillStyle = settings.lightMode ? colors.at(0) : colors.at(-1)
            ctx.fillText(msgText.value, mx, my)
        }

        prevFrame = timestamp
        frame = requestAnimationFrame(drawBubbles)
    }

    function stop() {
        if (frame !== null) {
            cancelAnimationFrame(frame)
            frame = null
        }
        sounds.stop(SOUND.MENU_MUSIC)
        prevFrame = null
        particles = []
    }
    function init() {
        stop()
        if (props.showEffects) {
            switch(isWin.value) {
                case GAME_RESULT.WIN:
                    dirX = 0
                    dirY = -1
                    colors = ["#185519", "#387F39", "#F6E96B", "#BEDC74"]
                    direction = "top"
                    break;
                case GAME_RESULT.DRAW:
                    dirX = 1
                    dirY = 0
                    colors = ["#2D336B", "#7886C7", "#A9B5DF"]
                    direction = "right"
                    break;
                case GAME_RESULT.LOSS:
                    dirX = 0
                    dirY = 1
                    colors = ["#7D0A0A", "#BF3131", "#F2B28C"]
                    direction = "bottom"
                    break;
            }
            ctx = el.value.getContext("2d")
            fontSize = Math.min(props.effectsHeight, props.effectsWidth) > 100 ? 28 : 18
            ctx.font = `bold ${fontSize}px sans-serif`
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            minRadius = Math.max(5, Math.min(props.effectsHeight, props.effectsWidth) * 0.05)
            maxRadius = minRadius * 5
            frame = requestAnimationFrame(drawBubbles)
            sounds.stop(SOUND.MENU_MUSIC)
            setTimeout(() => sounds.play(SOUND.MENU_MUSIC, false), 500)
        }
    }

    onMounted(init)
    onUnmounted(stop)

</script>