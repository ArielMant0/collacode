<template>
    <Teleport to="body">
        <div v-if="model" ref="el" class="my-tt" :style="{ top: py+'px', left: px+'px', maxWidth: maxWidth+'px', position: 'absolute', zIndex: zIndex }">
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
        align: {
            type: String,
            default: "right"
        }

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

    const tw = ref(Math.min(250, props.maxWidth))

    const px = computed(() => {
        if (!el.value) return props.x
        if (tx.value < 0) {
            if (props.align === "left") {
                return props.x - tw.value < 0 ?
                    props.x + 15 :
                    props.x - tw.value
            }
            return props.x + 15
        }
        return tx.value
    })
    const py = computed(() => {
        if (!el.value) return props.y
        return ty.value >= 0 ? ty.value : props.y + 5
    })

    function checkPosition() {
        if (!model.value) return

        if (!el.value) {
            checkCount++
            return checkCount < 5 ? setTimeout(checkPosition, 25) : null
        }

        checkCount = 0;

        const { width, height } = el.value.getBoundingClientRect()

        const ww = window.innerWidth + window.scrollX
        const wh = window.innerHeight + window.scrollY

        if (props.y + height + 5 > wh) {
            ty.value = wh - height - 5
        } else {
            ty.value = -1;
        }

        if (props.align === "left" || props.x + width + 10 > ww) {
            tx.value = props.x - width - 10
            if (tx.value < 0 && props.y - height - 5 >= 0) {
                ty.value = props.y - height - 5
            }
        } else {
            tx.value = -1
        }
        tw.value = width

    }

    watch(() => ([props.x, props.y]), checkPosition)
    watch(model, checkPosition)

    watch(() => props.data, function() {
        let show = false;
        switch (typeof props.data) {
            case 'string':
                show = props.data.length > 0
                break;
            case 'bigint':
            case 'number':
                show = true;
                break;
            case 'boolean':
                show = props.data
                break;
            case 'undefined':
                show = false;
                break;
            default:
                show = props.data !== null
        }

        tx.value = -1
        ty.value = -1
        if (model.value !== show) {
            model.value = show
        }
    }, { deep: true })

</script>

<style scoped>
.my-tt {
    transition-property: left, top;
    transition-duration: 200ms;
    transition-timing-function: ease-out;
}
</style>
