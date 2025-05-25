<template>
    <Teleport to="body">
        <v-sheet v-if="model" ref="el" class="my-tt pa-1" rounded="sm" elevation="2" :style="{
                top: py+'px',
                left: px+'px',
                minHeight: minHeight+'px',
                maxHeight: maxHeight+'px',
                minWidth: minWidth+'px',
                maxWidth: maxWidth+'px',
                overflowY: 'auto',
                position: 'absolute',
                zIndex: zIndex,
                marginLeft: '2px',
                marginTop: '2px',
                marginRight: '6px',
                marginBottom: '6px'
            }">
            <slot>
                <div v-html="data"></div>
            </slot>
        </v-sheet>
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
        minHeight: {
            type: Number,
            default: 25
        },
        maxHeight: {
            type: Number,
            default: 600
        },
        minWidth: {
            type: Number,
            default: 200
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
            default: 3999
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
    const tmpLeft = ref(false)

    let checkCount = 0, reposCount = 0

    const tw = ref(Math.min(250, props.minWidth))

    const px = computed(() => {
        if (!el.value) return props.x
        if (tx.value < 0) {
            if (tmpLeft.value || props.align === "left") {
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
        return ty.value >= 0 ? ty.value : props.y + 10
    })

    function checkPosition() {
        if (!model.value) return

        if (!el.value) {
            checkCount++
            return checkCount < 5 ? setTimeout(checkPosition, 25) : null
        }

        checkCount = 0;

        const { width, height } = el.value.$el.getBoundingClientRect()

        const ww = window.innerWidth + window.scrollX
        const wh = window.innerHeight + window.scrollY

        const rh = Math.max(props.minHeight, height)
        const rw = Math.max(props.minWidth, width)

        let fx, fy;

        if (props.y + rh + 10 > wh) {
            fy = Math.max(0, wh - rh - 10)
        } else {
            fy = -1;
        }

        if (props.align === "left" || props.x + rw + 15 > ww) {
            fx = Math.max(0, props.x - rw - 15)
        } else {
            fx = -1
        }

        tmpLeft.value = props.align !== "left" && fx >= 0 && fy >= 0
        if (tmpLeft.value) {
            fx = Math.max(0, props.x - rw - 15)
            fy = Math.max(0, props.y - rh - 10)
            reposCount++
            if (reposCount < 3) {
                setTimeout(checkPosition, 250)
            }
        }

        tx.value = fx
        ty.value = fy

        tw.value = rw

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

        reposCount = 0
        checkCount = 0
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
