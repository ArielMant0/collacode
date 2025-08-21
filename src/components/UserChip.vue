<template>
    <span>
        <v-tooltip v-if="user" :text="user.name" location="top" open-delay="300">
            <template v-slot:activator="{ props }">
                <v-chip v-bind="props"
                    :variant="model ? 'flat' : 'outlined'"
                    :size="small ? 'small' : 'default'"
                    :class="{'cursor-pointer': selectable }"
                    @click="onClick"
                    @pointerenter="onEnter"
                    @pointerleave="onLeave"
                    density="compact"
                    :color="user.color">
                    {{ short ? user.short : user.name }}
                </v-chip>
            </template>
        </v-tooltip>
    </span>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { onMounted, watch } from 'vue';

    const app = useApp()

    const model = defineModel({ type: Boolean, default: true })
    const props = defineProps({
        id: {
            type: Number,
            required: true
        },
        short: {
            type: Boolean,
            default: false
        },
        small: {
            type: Boolean,
            default: false
        },
        selectable: {
            type: Boolean,
            default: false
        },
    })

    const emit = defineEmits(["click", "hover"])

    const user = ref(null)

    function read() {
        user.value = app.getUser(props.id)
        model.value = true
    }

    function onClick(event) {
        if (props.selectable) {
            model.value = !model.value
        }
        emit("click", props.id, event, model.value)
    }
    function onEnter(event) {
        emit("hover", props.id, event)
    }
    function onLeave(event) {
        emit("hover", null, event)
    }

    onMounted(read)

    watch(() => props.id, read)
</script>