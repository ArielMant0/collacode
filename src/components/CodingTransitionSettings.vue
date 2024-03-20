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
    </div>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { useLoader } from '@/use/loader';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, ref } from 'vue';

    const app = useApp();
    const loader = useLoader();
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
        if (app.transitionCode) {
            await loadTagGroups(app.transitionCode);
            await loadCodeTransitions();
            app.setReloaded("coding")
        }
    }

    async function loadTagGroups(code) {
        const result = await loader.get(`tag_groups/old/${app.activeCode}/new/${code}`);
        DM.setData("tag_groups", result);
        return app.setReloaded("tag_groups")
    }

    async function loadCodeTransitions() {
        const result = await loader.get(`code_transitions/code/${app.activeCode}`);
        DM.setData("code_transitions", result);
        return app.setReloaded("code_transitions")
    }

    async function setTransitionCode(id) {
        app.setTransitionCode(id);
        app.needsReload("coding")
    }

    onMounted(function() {
        editExisting.value = filteredCodes.value.length > 0;
    })

    watch(() => ([dataNeedsReload.value._all, dataNeedsReload.value.coding]), loadAll, { deep: true });
    watch(() => dataNeedsReload.value.tag_groups, loadTagGroups);
    watch(() => dataNeedsReload.value.code_transitions, loadCodeTransitions);
</script>