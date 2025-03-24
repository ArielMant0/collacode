<template>
    <div :style="{ width: width, height: height, minWidth: '300px' }" class="d-flex align-center justify-center flex-column">
        <div class="loading-screen"></div>
        <v-sheet v-if="mixed.length > 0" class="text-caption mt-8 pa-2" color="surface-light" rounded style="width: 80%; min-width: 100px; text-align: center;">
            <i v-html="mixed[msgIdx]"></i>
        </v-sheet >
    </div>
</template>

<script setup>
    import { randomShuffle } from '@/use/random';
    import { onMounted, onUnmounted, watch } from 'vue';

    const props = defineProps({
        messages: {
            type: Array,
            default: () => ([])
        },
        messageInterval: {
            type: Number,
            default: 2000
        },
        width: {
            type: String,
            default: "75%"
        },
        height: {
            type: String,
            default: "80vh"
        }
    })

    let int = null

    const msgIdx = ref(0)
    const mixed = ref([])

    function nextMessage() {
        msgIdx.value = msgIdx.value < mixed.value.length-1 ? msgIdx.value+1 : 0
    }

    function clear() {
        msgIdx.value = 0;
        if (int !== null) {
            clearInterval(int)
            int = null
        }
    }
    function init() {
        clear()
        if (props.messages.length > 0) {
            mixed.value = randomShuffle(props.messages.slice())
            int = setInterval(nextMessage, props.messageInterval)
        } else {
            mixed.value = []
        }
    }

    onUnmounted(clear)

    onMounted(init)

    watch(() => props.messages, init, { deep: true })
    watch(() => props.messageInterval, init)
</script>