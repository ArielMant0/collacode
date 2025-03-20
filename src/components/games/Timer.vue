<template>
    <v-sheet
        style="font-size: x-large;"
        class="mb-4 pt-4 pb-4 pr-8 pl-8"
        rounded="sm"
        :color="props.showCritical && secondsLeft < critical ? props.criticalColor : props.color">
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
            default: "#ed5a5a"
        },
        color: {
            type: String,
            default: "surface-light"
        },
        showCritical: {
            type: Boolean,
            default: true
        },
        critical: {
            type: Number,
            default: 5
        },
    })
    const emit = defineEmits(["start", "pause", "stop", "tick", "end"])

    const timeEnd = ref(DateTime.local())
    const timer = ref(DateTime.local())

    const secondsLeft = computed(() => timer.value.minutes*60 + timer.value.seconds)

    let int = null, lastSecond = null

    function tick() {
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        if (secondsLeft.value <= 0) {
            stop("end")
            lastSecond = null
            sounds.stop(SOUND.TICK, false)
        } else if (secondsLeft.value <= props.critical) {
            const s = Math.floor(timer.value.seconds)
            if (lastSecond === null) {
                lastSecond = Math.floor(timer.value.seconds)
                sounds.play(SOUND.TICK, false)
            } else if (s < lastSecond) {
                lastSecond = s
                sounds.play(SOUND.TICK, false)
            }
            emit("tick", secondsLeft.value)
        } else {
            emit("tick", secondsLeft.value)
        }
    }
    function start() {
        if (int !== null) {
            clearInterval(int)
            int = null;
        }
        lastSecond = null
        timeEnd.value = DateTime.local().plus({ seconds: props.timeInSec })
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        int = setInterval(tick, 200)
        emit("start")
    }
    function pause() {
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        if (int === null) {
            int = setInterval(tick, 200)
            emit("pause")
        } else {
            stop("pause")
        }
    }
    function stop(emitName="stop") {
        lastSecond = null
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        if (int !== null) {
            clearInterval(int)
            int = null;
            emit(emitName)
        }
    }

    onUnmounted(stop)

    defineExpose({ start, pause, stop })

</script>