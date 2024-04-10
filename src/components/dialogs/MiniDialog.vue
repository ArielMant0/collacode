<template>
    <v-dialog v-model="model"
        :min-width="minWidth"
        width="auto"
        elevation="8"
        density="compact"
        >
        <v-card :title="title">
            <v-card-text>
                <slot name="text">
                    {{ text }}
                </slot>
            </v-card-text>

            <v-card-actions v-if="!noActions">
                <slot name="actions">
                    <v-btn class="ms-2" :color="cancelColor" @click="emit('cancel')">{{ cancelText }}</v-btn>
                    <v-btn class="ms-auto" :color="submitColor" @click="emit('submit')">{{ submitText }}</v-btn>
                </slot>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup>

    const model = defineModel();
    const props = defineProps({
        title: {
            type: String,
        },
        text: {
            type: String,
            default: ""
        },
        cancelText: {
            type: String,
            default: "cancel"
        },
        cancelColor: {
            type: String,
            default: "warning"
        },
        submitText: {
            type: String,
            default: "submit"
        },
        submitColor: {
            type: String,
            default: "primary"
        },
        minWidth: {
            type: [Number, String],
            default: 250
        },
        noActions: {
            type: Boolean,
            default: false
        }
    })

    const emit = defineEmits(["submit", "cancel"])
</script>