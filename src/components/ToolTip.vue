<template>
    <Teleport to="body">
        <div v-if="model" ref="el" :style="{ top: py+'px', left: px+'px', maxWidth: maxWidth+'px', position: 'absolute', zIndex: zIndex }">
            <v-sheet class="pa-1" rounded="sm" elevation="2">
                <slot>
                    <div v-html="data"></div>
                </slot>
            </v-sheet>
        </div>
    </Teleport>
</template>

<script setup>
    import { onClickOutside } from '@vueuse/core';
    import { computed, watch } from 'vue';

    const model = defineModel()
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
        maxWidth: {
            type: Number,
            default: 600
        },
        closeOnOutsideClick: {
            type: Boolean,
            default: false
        },
        zIndex: {
            type: Number,
            default: 2999
        },
    })
    const emit = defineEmits(["close"])

    const el = ref(null)

    onClickOutside(el, function() {
        if (props.closeOnOutsideClick) {
            model.value = false;
        }
        emit("close")
    })


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
    watch(() => props.data, function() {
        const show = props.data !== null && props.data !== ''
        if (model.value !== show) {
            model.value = show
        }
    })

</script>
