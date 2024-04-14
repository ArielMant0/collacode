<template>
    <div class="d-flex flex-column">
        <v-checkbox v-model="editExisting"
            :disabled="filteredCodes.length === 0"
            label="from existing"
            hide-details
            hide-spin-buttons
            class="mr-2"
            density="compact"/>

        <div v-if="editExisting && filteredCodes">
            <CodeWidget
                :codes="filteredCodes"
                :initial="transitionCode"
                @select="setTransitionCode"
                can-edit
                />
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
    import { useLoader } from '@/use/loader';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, ref } from 'vue';
    import { useToast } from 'vue-toastification';
    import CodeWidget from './CodeWidget.vue';

    const app = useApp();
    const loader = useLoader();
    const toast = useToast();
    const { codes, transitionCode } = storeToRefs(app)

    const editExisting = ref(false);
    const newCodeName = ref("")
    const newCodeDesc = ref("")

    const filteredCodes = computed(() => codes.value.filter(d =>  d.id !== app.activeCode))

    async function createNewCode() {
        if (newCodeName.value) {
            const code = {
                name: newCodeName.value,
                description: newCodeDesc.value,
                created: Date.now(),
                created_by: app.activeUserId
            }

            await loader.post("add/codes", { dataset: app.ds, rows: [code] })
            toast.success("created new code " + newCodeName.value)
            app.addAction("set transition code", { name: newCodeName.value })
            newCodeName.value = "";
            newCodeDesc.value = "";
            app.needsReload("codes");
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

    function resolveActionQueue() {
        let action = app.popAction();
        do {
            switch(action.action) {
                case "set transition code":
                    editExisting.value = true;
                    if (action.values.id) {
                        setTransitionCode(action.values.id)
                    } else {
                        const c = codes.value.find(d => d.name === action.values.name);
                        if (c) {
                            setTransitionCode(c.id);
                        }
                    }
                    break;
            }
            action = app.popAction();
        } while (action)
    }

    onMounted(function() {
        editExisting.value = filteredCodes.value.length > 0;
        if (!transitionCode.value && filteredCodes.value.length > 0) {
            setTransitionCode(filteredCodes.value.at(-1).id);
        }
    })

    watch(() => app.dataLoading.codes, function(val) {
        if (val === false && app.hasActions) {
            resolveActionQueue();
        }
    })
</script>