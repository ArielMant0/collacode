<template>
    <v-btn v-if="model"
        :variant="variant"
        :density="density"
        :color="color"
        :disabled="disabled"
        :prepend-icon="prependIcon"
        :size="size"
        :rounded="rounded"
        class="pl-2 pr-2 pt-1 pb-1"
        @click="e => emit('click', e)">
        {{ text }}
    </v-btn>
    <v-btn v-else
        :variant="variant"
        :density="density"
        :color="color"
        :disabled="disabled"
        :icon="icon"
        :size="size"
        :rounded="rounded"
        style="max-width: 25px !important;"
        @click="e => emit('click', e)">
    </v-btn>
</template>

<script setup>
    const model = defineModel({ default: true })
    const props = defineProps({
        text: { type: String, default: "" },
        variant: { type: [String, null], default: null },
        density: { type: [String, null], default: "comfortable" },
        color: { type: [String, null], default: "default" },
        disabled: { type: Boolean, default: false },
        size: { type: [String, null], default: null },
        rounded: { type: [String, null], default: null },
        icon: { type: [String, null], default: null },
        prependIcon: { type: [String, null], default: null },
    })

    const emit = defineEmits(["click"])
</script>