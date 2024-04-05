<template>
    <div class="d-flex flex-column pa-2">
        <h4>Transition Code</h4>
        <v-checkbox v-model="editExisting"
            :disabled="filteredCodes.length === 0"
            label="from existing"
            hide-details
            hide-spin-buttons
            class="mr-2"
            density="compact"/>

        <div v-if="editExisting">
            <v-select :model-value="transitionCode"
                :items="filteredCodes"
                label="Existing Codes"
                item-title="name"
                item-value="id"
                class="mb-1"
                hide-details
                hide-no-data
                hide-spin-buttons
                @update:model-value="setTransitionCode"/>
            <v-textarea :model-value="transCodeDesc"
                density="compact"
                label="Code Description"
                style="width: 100%"
                readonly
                class="cursor-default"
                hide-details
                hide-spin-buttons/>
        </div>

        <div v-else>
            <v-text-field v-model="newCodeName"
                density="compact"
                class="mb-1"
                label="New Code Name"
                style="width: 100%"
                hide-details
                hide-spin-buttons/>
            <v-textarea v-model="newCodeDesc"
                density="compact"
                class="mb-1"
                label="New Code Description"
                style="width: 100%"
                hide-details
                hide-spin-buttons/>
            <v-btn color="primary" block @click="createNewCode">create</v-btn>
        </div>

        <v-btn block :color="transitionCode ? 'primary' : 'default'"
            class="mt-2"
            :disabled="!transitionCode"
            @click="finalize">
            finalize transition
        </v-btn>
    </div>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { useLoader } from '@/use/loader';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, ref } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp();
    const loader = useLoader();
    const toast = useToast();
    const { codes, transitionCode, dataNeedsReload } = storeToRefs(app)

    const editExisting = ref(false);
    const newCodeName = ref("")
    const newCodeDesc = ref("")

    const filteredCodes = computed(() => codes.value.filter(d => d.id !== app.activeCode))
    const transCodeDesc = computed(() => {
        if (transitionCode.value) {
            return app.codes.find(d => d.id === transitionCode.value).description
        }
        return ""
    })

    function createNewCode() {
        if (newCodeName.value) {

            const name = newCodeName.value;
            newCodeName.value = "";
            newCodeDesc.value = "";

            const code = {
                name: name,
                description: newCodeDesc.value,
                created: Date.now(),
                created_by: app.activeUserId
            }
            loader.post("add/codes", { dataset: app.ds, rows: [code] })
                .then(() => {
                    app.needsReload("codes");
                    const c = app.codes.find(d => d.name === name);
                    if (c) {
                        app.setTransitionCode(c.id);
                    }
                })
        }
    }

    async function loadAll() {
        await loadCodeTransitions();
        await Promise.all([loadTags(), loadOldTags(), loadTagAssignments()]);
        await loadDataTags();
        app.setReloaded("transition")
    }

    async function loadTags() {
        if (app.activeCode === null || transitionCode.value === null) return;
        const result = await loader.get(`tags/code/${transitionCode.value}`);
        DM.setData("tags", result);
        return app.setReloaded("tags")
    }
    async function loadOldTags() {
        if (app.activeCode === null || transitionCode.value === null) return;
        const result = await loader.get(`tags/code/${app.activeCode}`);
        DM.setData("tag_old", result);
        return app.setReloaded("tag_old")
    }
    async function loadDataTags() {
        if (app.activeCode === null || transitionCode.value === null) return;
        const result = await loader.get(`datatags/code/${transitionCode.value}`);
        DM.setData("datatags", result);
        return app.setReloaded("datatags")
    }
    async function loadTagAssignments() {
        if (app.activeCode === null || transitionCode.value === null) return;
        const result = await loader.get(`tag_assignments/old/${app.activeCode}/new/${transitionCode.value}`);
        DM.setData("tag_assignments", result);
        return app.setReloaded("tag_assignments")
    }
    async function loadCodeTransitions() {
        if (!app.ds) return;
        if (app.activeCode === null) {
            const result = await loader.get(`code_transitions/dataset/${app.ds}`);
            DM.setData("code_transitions", result);
            return app.setReloaded("code_transitions")
        } else if (app.transitionCode === null) {
            const result = await loader.get(`code_transitions/code/${app.activeCode}`);
            DM.setData("code_transitions", result);
            return app.setReloaded("code_transitions")
        } else {
            const result = await loader.get(`code_transitions/old/${app.activeCode}/new/${transitionCode.value}`);
            DM.setData("code_transitions", result);
            return app.setReloaded("code_transitions")
        }
    }

    async function setTransitionCode(id) {
        app.setTransitionCode(id);
        await start();
        app.needsReload("transition")
    }

    async function start() {
        if (app.activeCode && transitionCode.value) {
            await loader.post(`start/codes/transition/old/${app.activeCode}/new/${transitionCode.value}`);
        }
    }

    function finalize() {
        if (app.activeCode && transitionCode.value) {
            loader.post(`finalize/codes/transition/old/${app.activeCode}/new/${transitionCode.value}`, { created_by: app.activeUserId, created: Date.now() })
                .then(() => toast.success("finalized code transition"))
        }
    }

    onMounted(function() {
        editExisting.value = filteredCodes.value.length > 0;
    })

    watch(() => dataNeedsReload.value._all, loadAll);
    watch(() => dataNeedsReload.value.transition, loadAll);
    watch(() => dataNeedsReload.value.old_tags, loadOldTags);
    watch(() => dataNeedsReload.value.tag_assignments, loadTagAssignments);
    watch(() => dataNeedsReload.value.code_transitions, loadCodeTransitions);
</script>