<template>
    <v-sheet
        style="font-size: x-large;"
        class="mb-4 pt-4 pb-4 pr-8 pl-8"
        rounded="sm"
        :color="props.showCritical && secondsLeft < 10 ? props.criticalColor : props.color">
        {{ secondsLeft > 0 ? timer.toFormat("mm:ss") : "--:--" }}
    </v-sheet>
</template>

<script setup>
    import { DateTime } from 'luxon';
    import { computed } from 'vue';

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
            default: false
        }
    })
    const emit = defineEmits(["start", "pause", "stop", "tick", "end"])

    const timeEnd = ref(DateTime.local())
    const timer = ref(DateTime.local())

    const secondsLeft = computed(() => timer.value.minutes*60 + timer.value.seconds)

    let int = null;

    function tick() {
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        if (secondsLeft.value <= 0) {
            stop("end")
        } else {
            emit("tick", secondsLeft.value)
        }
    }
    function start() {
        if (int !== null) {
            clearInterval(int)
            int = null;
        }
        timeEnd.value = DateTime.local().plus({ seconds: props.timeInSec })
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        int = setInterval(tick, 1000)
        emit("start")
    }
    function pause() {
        if (int === null) {
            int = setInterval(tick, 1000)
            emit("pause")
        } else {
            stop("pause")
        }
    }
    function stop(emitName="stop") {
        if (int !== null) {
            clearInterval(int)
            int = null;
            emit(emitName)
        }
    }

    defineExpose({ start, pause, stop })

</script>