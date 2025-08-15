<template>
    <v-tooltip :text="desc" :location="location" :open-delay="openDelay">
        <template #activator="{ props }">
            <span>
                <v-icon v-bind="props"
                    :color="color"
                    :class="{ 'cursor-pointer': !preventClick }"
                    @click="onClick"
                    :size="size">
                    {{ icon }}
                </v-icon>
                <span v-if="label" class="ml-1">{{ text }}</span>
            </span>
        </template>
    </v-tooltip>
</template>

<script setup>
    import { EVIDENCE_TYPE, getEvidenceTypeColor, useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { computed, onMounted, watch } from 'vue';

    const app = useApp()

    const props = defineProps({
        type: { type: Number },
        id: { type: Number },
        evidence: { type: Object },
        size: { type: String, default: "default" },
        location: { type: String, default: "top" },
        openDelay: { type: Number, default: 300 },
        useUserColor: { type: Boolean, default: false },
        preventClick: { type: Boolean, default: false },
        label: { type: Boolean, default: false },
    })

    const emit = defineEmits(["click"])

    const value = ref(EVIDENCE_TYPE.POSITIVE)
    const user = ref(0)

    const color = computed(() => {
        if (props.useUserColor) {
            return app.getUserColor(user.value)
        }
        return getEvidenceTypeColor(value.value)
    })
    const text = computed(() => value.value === EVIDENCE_TYPE.NEGATIVE ?
        "negative evidence" :
        "positive evidence"
    )
    const desc = computed(() => text.value + (props.preventClick ? "" : " - click to toggle"))
    const icon = computed(() => value.value === EVIDENCE_TYPE.NEGATIVE ?
        "mdi-close-circle" :
        "mdi-check-circle"
    )

    function onClick() {
        if (props.preventClick) return
        emit('click', value.value)
    }

    function read() {
        if (props.type) {
            value.value = props.type
        } else if (props.evidence) {
            value.value = props.evidence.type
        } else if (props.id) {
            const ev = DM.getDataBy("evidence", d => d.id === props.id)
            value.value = ev ? ev.type : EVIDENCE_TYPE.POSITIVE
        }
    }

    onMounted(read)

    watch(props, read)
</script>