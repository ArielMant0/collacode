<template>
    <div class="pa-2">

        <v-select v-if="!addNew"
            v-model="selected"
            :items="transitions"
            class="mt-2"
            density="compact"
            hide-details
            @update:model-value="setTransition"
            item-title="name"
            item-value="id"/>

        <v-checkbox v-if="allowCreate"
            v-model="addNew"
            label="start a new transition"
            density="compact"
            @update:model-value="prepareCodeData"
            hide-details
            hide-spin-buttons/>

        <div class="mt-2" v-if="allowCreate && addNew && activeCode">

            <v-text-field :model-value="app.getCodeName(activeCode)"
                class="mb-1"
                hide-details
                hide-spin-buttons
                label="Starting Code"
                disabled
                density="compact"/>

            <v-text-field v-model="codeData.name"
                class="mb-1"
                hide-details
                hide-spin-buttons
                label="New Code Name"
                density="compact"/>

            <v-text-field :model-value="app.getUserName(codeData.created_by)"
                class="mb-1"
                hide-details
                hide-spin-buttons
                label="Creator"
                disabled
                density="compact"/>

            <v-textarea v-model="codeData.description"
                hide-details
                hide-spin-buttons
                density="compact"
                label="Code Description"
                class="mb-2"/>

            <v-btn color="primary"
                density="compact"
                class="mt-2"
                block
                :disabled="!activeCode || !codeData.name || !codeData.description"
                @click="startTransition">start</v-btn>

        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import { startCodeTransition } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { ref, onMounted, watch, reactive, computed } from 'vue';
    import { useToast } from 'vue-toastification';

    const toast = useToast();
    const times = useTimes();
    const app = useApp();
    const settings = useSettings()
    const { activeCode } = storeToRefs(app)

    const props = defineProps({
        initial: {
            type: Number
        },
        allowCreate: {
            type: Boolean,
            default: false
        },

    });
    const emit = defineEmits(["select", "create", "create-code"])

    const addNew = ref(false)

    const selected = ref(props.initial);
    const codeData = reactive({
        name: "",
        description: "",
        created_by: app.activeUserId,
        created: Date.now(),
    })

    const transitions = computed(() => {
        if (!activeCode.value) return []
        return app.transitions.filter(d => d.old_code == activeCode.value || d.new_code === activeCode.value)
    })

    let toastId;

    function setTransition(id) {
        app.setActiveTransition(id)
        emit("select", id);
        times.needsReload("all")
    }
    function check() {
        if (props.initial && (!selected.value || !transitions.value.some(d => d.id === selected.value))) {
            selected.value = props.initial;
        }
    }

    function prepareCodeData() {
        codeData.name = "";
        codeData.description = "";
        codeData.created_by = app.activeUserId;
        codeData.created = Date.now();
    }

    async function startTransition() {
        if (!activeCode.value) {
            return toast.error("start code missing")
        }

        if (!codeData.name) {
            return toast.error("new code name missing")
        }
        if (!codeData.description) {
            return toast.error("new code description missing")
        }

        try {
            settings.isLoading = true;
            toastId = toast("preparing transition, this may take a while...", { timeout: false })
            await startCodeTransition(activeCode.value, codeData)
            app.addAction("trans widget", "set trans", { name: codeData.name })
            settings.isLoading = false;
            addNew.value = false;
            emit("create", activeCode.value);
            toast.dismiss(toastId)
            toastId = null
            toast.success("created code transition")
            times.needsReload("transitioning")
        } catch {
            settings.isLoading = false;
            toast.error(`error starting transition from "${activeCode.value}" to "${codeData.name}"`)
        }
    }

    function processActions() {
        let action = app.popAction("trans widget");
        while (action) {
            switch (action.action) {
                case "set trans": {
                    const item = app.transitions.find(d => d.name === action.values.name)
                    if (item) {
                        app.setActiveCode(item.new_code)
                    }
                }
                default: break;
            }
            action = app.popAction("trans widget");
        }
    }

    onMounted(check)

    watch(() => props.initial, check)
    watch(() => times.transitioning, processActions);
</script>