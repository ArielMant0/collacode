<template>
    <v-sheet
        style="font-size: x-large;"
        class="mb-4 pt-3 pb-3 pr-6 pl-6 d-flex align-center"
        rounded
        :color="props.showCritical && secondsLeft < critical ? props.criticalColor : props.color">
        <v-icon class="mr-1" :class="secondsLeft < critical ? 'wobble-fast' : ''">{{ icon }}</v-icon>
        {{ secondsLeft > 0 ? timer.toFormat("mm:ss") : "--:--" }}
    </v-sheet>
</template>

<script setup>
    import { SOUND, useSounds } from '@/store/sounds';
    import { DateTime } from 'luxon';
    import { computed, onUnmounted } from 'vue';

    const sounds = useSounds()

    const props = defineProps({
        timeInSec: {
            type: Number,
            default: 60
        },
        criticalColor: {
            type: String,
            default: "error"
        },
        color: {
            type: String,
            default: "surface-light"
        },
        icon: {
            type: String,
            default: "mdi-alarm"
        },
        showCritical: {
            type: Boolean,
            default: true
        },
        critical: {
            type: Number,
            default: 5
        },
        warning: {
            type: Number,
            default: 10
        },
    })
    const emit = defineEmits(["start", "pause", "stop", "tick", "end"])

    const timeEnd = ref(DateTime.local())
    const timer = ref(DateTime.local())

    const secondsLeft = computed(() => timer.value.minutes*60 + timer.value.seconds)

    let int = null, lastSecond = props.timeInSec

    function tick() {
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        const s = Math.floor(secondsLeft.value)

        if (secondsLeft.value <= 0) {
            sounds.stop(SOUND.TICK, false)
            stop("end")
            return
        } else if (s === props.warning && s < lastSecond) {
            // play a tick sound for critical seconds
            sounds.play(SOUND.OBACHT, false)
        } else if (secondsLeft.value <= props.critical && s < lastSecond) {
            // play a tick sound for critical seconds
            sounds.play(SOUND.TICK, false)
        }

        // emit tick when seconds change
        if (s < lastSecond) {
            lastSecond = s;
            emit("tick", secondsLeft.value)
        }
        int = requestAnimationFrame(tick)
    }
    function start() {
        if (int !== null) {
            cancelAnimationFrame(int)
            int = null;
        }
        timeEnd.value = DateTime.local().plus({ seconds: props.timeInSec })
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        lastSecond = Math.floor(secondsLeft.value)
        int = requestAnimationFrame(tick)
        emit("start")
    }
    function pause() {
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        if (int === null) {
            int = requestAnimationFrame(tick)
            emit("pause")
        } else {
            stop("pause")
        }
    }
    function stop(emitName="stop") {
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        lastSecond = Math.floor(secondsLeft.value)
        if (int !== null) {
            cancelAnimationFrame(int)
            int = null;
            emit(emitName)
        }
    }

    onUnmounted(stop)

    defineExpose({ start, pause, stop })

</script>

<style scoped>
.wobble-fast {
  animation: wobble 300ms infinite;
}</style>