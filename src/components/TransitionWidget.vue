<template>
    <div class="pa-2">
        <v-checkbox v-if="allowCreate"
            v-model="addNew"
            label="start a new transition"
            density="compact"
            hide-details
            hide-spin-buttons/>
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
                @update:model-value="checkCodesAvailable"
                item-title="name"
                item-value="id"/>
            <v-checkbox v-model="createCode"
                label="create new coding"
                density="compact"
                hide-details
                hide-spin-buttons
                :disabled="!oldCode"
                @update:model-value="prepareCodeData"
                />
            <div v-if="createCode">
                <v-text-field v-model="codeData.name"
                    class="mb-1"
                    hide-details
                    hide-spin-buttons
                    label="Name"
                    density="compact"/>

                <v-text-field :model-value="app.getUserName(codeData.created_by)"
                    class="mb-1"
                    hide-details
                    hide-spin-buttons
                    label="Author"
                    disabled
                    density="compact"/>

                <v-textarea v-model="codeData.description"
                    hide-details
                    hide-spin-buttons
                    density="compact"
                    label="Description"
                    class="mb-2"/>

                <v-btn color="primary" density="compact"
                    class="mt-2"
                    block
                    :disabled="!codeData.name || !codeData.description"
                    @click="createNewCode">create</v-btn>
            </div>
            <div v-else>
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
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { useLoader } from '@/use/loader'
    import { addCodes, startCodeTransition } from '@/use/utility';
    import Cookies from 'js-cookie';
    import { ref, computed, onMounted, watch, reactive } from 'vue';
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
    const emit = defineEmits(["select", "create", "create-code"])

    const app = useApp();
    const toast = useToast();
    const times = useTimes();

    const addNew = ref(false)
    const createCode = ref(false)
    const oldCode = ref(undefined)
    const newCode = ref(undefined)

    const selected = ref(props.initial);
    const codeData = reactive({
        name: "",
        description: "",
        created_by: app.activeUserId,
        created: Date.now(),
    })

    const otherCodes = computed(() => {
        if (!oldCode.value) return props.codes;
        return props.codes.filter(d => d.id !== oldCode.value && !getTransition(oldCode.value, d.id))
    })

    function checkCodesAvailable() {
        if (oldCode.value && otherCodes.value.length === 0) {
            createCode.value = true;
        }
    }
    function getTransition(oldC, newC) {
        return props.transitions.find(d => d.old_code == oldC && d.new_code == newC)
    }

    function setTransition(id) {
        emit("select", id);
        if (props.emitOnly) return;

        app.setActiveTransition(id)
        times.needsReload("all")
    }
    function check() {
        if (props.initial && (!selected.value || !props.transitions.some(d => d.id === selected.value))) {
            selected.value = props.initial;
        }
    }

    function prepareCodeData() {
        if (createCode.value) {
            codeData.name = "";
            codeData.description = "";
            codeData.created_by = app.activeUserId;
            codeData.created = Date.now();
        }
    }
    async function createNewCode() {
        if (!codeData.name || !codeData.description) {
            toast.error("missing code name or description")
            return
        }

        if (props.codes.find(d => d.name === codeData.name)) {
            toast.error(`code "${codeData.name}" already exists`)
            return;
        }

        app.addAction("trans widget", "set new code", { name: codeData.name });
        emit("create-code", codeData);

        if (props.emitOnly) return;

        codeData.created_by = app.activeUserId;
        codeData.created = Date.now();

        try {
            await addCodes(codeData)
            toast.success("addded new code")
            createCode.value = false;
            times.needsReload("codes")
        } catch {
            toast.error("error addding code")
        }
    }
    async function startTransition() {
        if (!oldCode.value || !newCode.value) {
            toast.error("missing codes")
            return;
        }

        const exists = getTransition(oldCode.value, newCode.value)
        if (exists) {
            toast.error(`transition "${exists.name}" already exists`)
            return;
        }

        emit("create", oldCode.value, newCode.value);
        if (props.emitOnly) return;

        try {
            await startCodeTransition(oldCode.value, newCode.value)
            toast.success("started code transition")
            addNew.value = false;
            times.needsReload()
        } catch {
            toast.error(`error starting transition from "${oldCode.value}" to "${newCode.value}"`)
        }
    }

    function processActions() {
        const toAdd = [];
        let action = app.popAction("trans widget");
        while (action) {
            switch (action.action) {
                case "set new code": {
                    const item = props.codes.find(d => d.name === action.values.name)
                    if (item) {
                        newCode.value = item.id;
                    } else {
                        toAdd.push(action)
                    }
                }
                default: break;
            }
            action = app.popAction("trans widget");
        }
        toAdd.forEach(d => app.addAction("trans widget", d.action, d.values));
    }

    onMounted(check)

    watch(() => props.initial, check)
    watch(() => props.initial, check)
    watch(() => times.codes, processActions);
</script>