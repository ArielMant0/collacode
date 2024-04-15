<template>
    <div class="pa-2">
        <v-checkbox v-if="allowCreate"
            v-model="addNew"
            label="start a new transition"
            density="compact"
            hide-details
            hide-spin-buttons
            />
        <v-select v-if="!addNew && transitions"
            v-model="selected"
            :items="transitions"
            class="mt-2"
            density="compact"
            hide-details
            @update:model-value="setTransition"
            item-title="name"
            item-value="id"/>
        <div class="mt-2" v-else-if="allowCreate && codes">
            <v-select v-model="oldCode"
                :items="codes"
                density="compact"
                label="from"
                hide-details
                item-title="name"
                item-value="id"/>
            <v-select v-model="newCode"
                :items="otherCodes"
                :disabled="!oldCode"
                label="to"
                class="mt-2"
                density="compact"
                hide-details
                item-title="name"
                item-value="id"/>
            <v-btn color="primary" density="compact"
                class="mt-2"
                block
                :disabled="!oldCode || !newCode"
                @click="startTransition">start</v-btn>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader'
    import { ref, computed, onMounted, watch } from 'vue';
import { useToast } from 'vue-toastification';

    const props = defineProps({
        initial: {
            type: Number
        },
        codes: {
            type: Array,
            required: true
        },
        transitions: {
            type: Array,
            required: true
        },
        allowCreate: {
            type: Boolean,
            default: false
        },
        emitOnly: {
            type: Boolean,
            default: false
        }
    });
    const emit = defineEmits(["select", "create"])

    const app = useApp();
    const loader = useLoader();
    const toast = useToast();

    const addNew = ref(false)
    const oldCode = ref(undefined)
    const newCode = ref(undefined)

    const selected = ref(props.initial);

    const otherCodes = computed(() => {
        if (!oldCode.value) return props.codes;
        return props.codes.filter(d => d.id !== oldCode.value && !getTransition(oldCode.value, d.id))
    })

    function getTransition(oldC, newC) {
        return props.transitions.find(d => d.old_code == oldC && d.new_code == newC)
    }

    function setTransition(id) {
        emit("select", id);
        if (props.emitOnly) return;

        app.setActiveTransition(id)
        app.needsReload("transition")
    }
    function check() {
        if (!selected.value && props.transitions.length > 0 && props.initial) {
            selected.value = props.initial;
        }
    }
    async function startTransition() {
        if (!oldCode.value || !newCode.value) return;

        const exists = getTransition(oldCode.value, newCode.value)
        if (exists) {
            toast.error(`transition "${exists.name}" already exists`)
            return;
        }

        emit("create", oldCode.value, newCode.value);
        if (props.emitOnly) return;

        await loader.post(`start/codes/transition/old/${oldCode.value}/new/${newCode.value}`);
        addNew.value = false;
        app.needsReload("transition")
    }

    onMounted(check)

    watch(() => props.initial, check)
</script>