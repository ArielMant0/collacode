<template>
    <v-dialog v-model="model"
        :min-width="minWidth"
        :max-width="maxWidth"
        width="auto"
        elevation="8"
        :scrim="!hideOverlay"
        density="compact">
        <v-card density="compact">
            <v-card-title v-if="title || closeIcon" style="min-height: 35px;">
                <div class="d-flex align-center">
                    <slot name="title">
                        <span>{{ title }}</span>
                    </slot>
                    <v-btn v-if="closeIcon"
                        style="position: absolute; top: 10px; right: 10px;"
                        @click="cancel"
                        density="compact"
                        variant="plain"
                        color="error"
                        rounded="sm"
                        icon="mdi-close"/>
                </div>
            </v-card-title>

            <v-card-text class="pt-2" :class="{ 'pb-4': noActions, 'pb-2': !noActions }">
                <div style="max-height: 85vh; overflow-y: auto;">
                    <slot name="text">
                        {{ text }}
                    </slot>
                </div>
            </v-card-text>

            <v-divider v-if="!noActions"></v-divider>

            <v-card-actions v-if="!noActions">
                <div>
                    <slot name="actions">
                        <v-btn v-if="cancelText.length > 0" :color="cancelColor" @click="cancel">{{ cancelText }}</v-btn>
                        <v-btn v-if="submitText.length > 0"class="ml-2" :color="submitColor" @click="submit">{{ submitText }}</v-btn>
                    </slot>
                </div>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { watch } from 'vue';

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
        maxWidth: {
            type: [Number, String],
            default: "95%"
        },
        noActions: {
            type: Boolean,
            default: false
        },
        closeIcon: {
            type: Boolean,
            default: false
        },
        hideOverlay: {
            type: Boolean,
            default: false
        }
    })

    const emit = defineEmits(["submit", "cancel"])
    const eventEmitted = ref(false)

    function cancel() {
        eventEmitted.value = true;
        model.value = false;
        emit('cancel')
    }
    function submit() {
        eventEmitted.value = true;
        model.value = false;
        emit('submit')
    }

    function checkCancel() {
        if (!model.value && !eventEmitted.value) {
            eventEmitted.value = true;
            emit('cancel')
        } else if (model.value) {
            eventEmitted.value = false;
        }
    }

    watch(model, checkCancel)
</script>