<template>
    <div class="pa-2">
        <v-select v-model="selected"
            class="mb-2"
            density="compact"
            hide-details
            :items="codes"
            item-title="name"
            item-value="id"
            hide-spin-buttons
            @update:model-value="onSelect"/>

        <v-text-field v-model="codeName"
            class="mb-1"
            hide-details
            hide-spin-buttons
            :label="nameLabel"
            :disabled="!codeData || !canEdit"
            density="compact"/>

        <v-text-field :model-value="codeCreator"
            class="mb-1"
            hide-details
            hide-spin-buttons
            :label="creatorLabel"
            disabled
            density="compact"/>

        <v-textarea v-model="codeDesc"
            :disabled="!canEdit || !codeData"
            hide-details
            hide-spin-buttons
            density="compact"
            :label="descLabel"
            class="mb-2"/>

        <div v-if="canEdit" class="d-flex justify-space-between">
            <v-btn append-icon="mdi-delete"
                class="mt-2 mr-1"
                :disabled="!codeData || !codeChanges"
                :color="codeChanges? 'error' : 'default'"
                @click="discard"
                >
                discard
            </v-btn>
            <v-btn :append-icon="buttonIcon"
                class="mt-2 ml-1"
                :disabled="!codeData || !codeChanges"
                :color="codeChanges? 'primary' : 'default'"
                @click="update"
                >
                {{ buttonLabel }}
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { ref, computed, onMounted, watch } from 'vue';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';

    const loader = useLoader();
    const toast = useToast();
    const app = useApp();
    const times = useTimes()

    const props = defineProps({
        initial: {
            type: Number,
            default: 0
        },
        nameLabel: {
            type: String,
            default: "Code Name"
        },
        creatorLabel: {
            type: String,
            default: "Code Creator"
        },
        descLabel: {
            type: String,
            default: "Code Description"
        },
        buttonLabel: {
            type: String,
            default: "sync"
        },
        buttonIcon: {
            type: String,
            default: "mdi-sync"
        },
        emitOnly: {
            type: Boolean,
            default: false
        },
        canEdit: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["select", "update", "discard"])

    const selected = ref(props.initial);
    const codeName = ref("");
    const codeDesc = ref("");
    const codeCreator = computed(() => codeData.value ? app.getUserName(codeData.value.created_by) : "")

    const codes = ref([])
    const codeData = computed(() => {
        if (!selected.value) return null;
        return codes.value.find(d => d.id === selected.value);
    })
    const codeChanges = computed(() => {
        if (!codeData.value) {
            return false;
        }
        return codeData.value.name !== codeName.value ||
            codeData.value.description !== codeDesc.value;
    });

    function readCodes() {
        codes.value = DM.getData("codes", false)
    }

    function read() {
        codeName.value = codeData.value ? codeData.value.name : "";
        codeDesc.value = codeData.value ? codeData.value.description : "";
    }

    function update() {
        if (codeData.value && codeChanges) {
            const obj = {
                id: selected.value,
                name: codeName.value,
                description: codeDesc.value,
            };
            emit("update", obj)
            if (props.emitOnly) return;

            loader.post("update/codes", { rows: [obj] })
                .catch(() => toast.error("invalid code name or description"))
                .then(() => {
                    toast.success("updated code " + codeName.value)
                    times.needsReload("codes")
                })
        }
    }
    function discard() {
        if (codeData.value) {
            codeName.value = codeData.value.name;
            codeDesc.value = codeData.value.description;
            emit("discard", codeData.value)
        }
    }
    function onSelect() {
        emit('select', selected.value)
        if (selected.value !== app.activeCode) {
            app.setActiveCode(selected.value);
            times.needsReload();
        }
        read()
    }

    onMounted(function() {
        readCodes();
        selected.value = props.initial;
        read()
    })

    watch(() => props.initial, function(now, prev) {
        if (prev === null) {
            selected.value = now;
            read();
        }
    });
    watch(() => Math.max(times.all, times.codes), readCodes);

</script>