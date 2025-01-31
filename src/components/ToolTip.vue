<template>
    <Teleport to="body">
        <div v-if="data !== null && data !== ''" ref="el" :style="{ top: py+'px', left: px+'px', maxWidth: maxWidth+'px' }" class="my-tooltip">
            <v-sheet class="pa-1" rounded="sm" elevation="2">
                <slot>
                    <div v-html="data"></div>
                </slot>
            </v-sheet>
        </div>
    </Teleport>
</template>

<script setup>
    import { computed, watch } from 'vue';

    const props = defineProps({
        x: {
            type: Number,
            required: true
        },
        y: {
            type: Number,
            required: true
        },
        data: {
            required: true
        },
        maxWidth:  {
            type: Number,
            default: 600
        },
    })

    const el = ref(null)

    const tx = ref(-1)
    const ty = ref(-1)
    let checkCount = 0;

    const px = computed(() => {
        if (!el.value) return props.x
        return tx.value > 0 ? tx.value : props.x
    })
    const py = computed(() => {
        if (!el.value) return props.y
        return ty.value > 0 ? ty.value : props.y
    })

    function checkPosition() {
        if (!el.value) {
            checkCount++
            return checkCount < 5 ? setTimeout(checkPosition, 25) : null
        }
        checkCount = 0;

        const { right, bottom, width, height } = el.value.getBoundingClientRect()

        if (right >= window.innerWidth-5) {
            tx.value = props.x - width - 30
        } else {
            tx.value = -1;
        }

        if (bottom >= window.innerHeight-5) {
            ty.value = props.y - height
        } else {
            ty.value = -1;
        }
    }

    watch(props, checkPosition, { deep: true })

</script>

<style scoped>
.my-tooltip {
    position: absolute;
    z-index: 4999;
}
</style>