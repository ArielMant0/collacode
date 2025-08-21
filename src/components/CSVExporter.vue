<template>
    <div>
        <v-overlay :model-value="isLoading" class="d-flex flex-column justify-center align-center" persistent>

            <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
            <div style="text-align: center; font-size: x-large; color: white;" class="mt-2">
                {{ status }}
            </div>

            <div v-if="filesToDo > 0" class="mt-8">
                <v-progress-linear :model-value="filesProcessed" size="256" color="primary"></v-progress-linear>
                <div style="text-align: center; font-size: x-large; color: white;" class="mt-2">
                    downloaded {{ filesDone }} of {{ filesToDo }} images
                </div>
            </div>
        </v-overlay>

        <v-card class="mb-2">
            <v-card-text>
                <div class="d-flex">
                    <v-select :model-value="ds"
                        class="mr-1"
                        density="compact"
                        hide-details
                        :items="datasets"
                        @update:model-value="app.setDataset"
                        item-title="name"
                        item-value="id"/>
                    <v-select :model-value="activeCode"
                        class="mr-1"
                        density="compact"
                        hide-details
                        :items="codes"
                        @update:model-value="app.setActiveCode"
                        item-title="name"
                        item-value="id"/>
                    <v-text-field v-model="filename" label="Filename" hide-details class="mr-1" hide-spin-buttons density="compact"/>
                    <v-select v-model="delim" label="Delimiter" :items="[';',',']" class="mr-1" hide-details hide-spin-buttons density="compact"/>
                </div>

                <h4 class="mt-8">Which data to you want to export?</h4>
                <div class="d-flex">
                    <v-chip v-for="opt in chosenOptions"
                        :key="opt.key"
                        density="compact"
                        class="text-caption mr-1 mb-1"
                        @click="opt.chosen = !opt.chosen"
                        :color="opt.chosen ? 'primary' : 'default'"
                        :variant="opt.chosen ? 'flat' : 'outlined'">
                        {{ opt.name }}
                    </v-chip>
                </div>

                <div v-if="chosenOptions.length > 0">
                    <v-checkbox v-model="exportImages"
                        label="include images"
                        hide-details
                        hide-spin-buttons
                        density="compact"/>
                </div>

            </v-card-text>

            <v-card-actions>
                <v-btn @click="exportData" color="primary" class="float-right">export</v-btn>
            </v-card-actions>
        </v-card>

        <v-card v-show="chosen.length > 0">
            <v-card-text>
                <div v-for="c in chosen" :key="'d_'+c.key">
                    <h3 class="mt-2">{{ c.name }} ({{ data[c.key].length }} rows)</h3>
                    <v-data-table :items="data[c.key]" density="compact">
                        <template v-slot:item.teaser="{ item }">
                            <ItemTeaser :item="item" prevent-click :width="100" :height="50" zoom-on-hover/>
                        </template>

                        <template v-slot:item.filepath="{ item }">
                            <EvidenceCell :item="item"
                                prevent-right-click
                                zoom-on-hover
                                :height="60"
                                :show-tag="false"
                                :image-fit="false"/>
                        </template>
                    </v-data-table>
                </div>
            </v-card-text>
        </v-card>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { computed, onMounted, reactive, ref, watch } from 'vue'
    import { saveAs } from 'file-saver';
    import JSZip from 'jszip';
    import axios from "axios";
    import * as api from '@/use/data-api';
    import { mediaPath } from '@/use/utility';
    import { useApp } from '@/store/app';
    import ItemTeaser from './items/ItemTeaser.vue';
    import { storeToRefs } from 'pinia';
    import EvidenceCell from './evidence/EvidenceCell.vue';
    import { useSettings } from '@/store/settings';

    const app = useApp()
    const settings = useSettings()
    const { ds, datasets, activeCode } = storeToRefs(app)
    const { isLoading } = storeToRefs(settings)

    const codes = ref([])

    const delim = ref(";")
    const filename = ref("export")

    const dataOptions = computed(() => {
        let basic = [
            { key: "items", name: app.itemNameCaptial+'s' },
            { key: "users", name: "Users" },
            { key: "tags", name: "Tags" },
            { key: "datatags", name: "Tag Assignments" },
            { key: "evidence", name: "Evidence" },
        ]

        if (ds.value) {
            basic = basic.slice(0, 2)
                .concat({ key: "codes", name: "Codes" })
                .concat(basic.slice(2))
        }

        return app.hasMetaItems ?
            basic.concat([
                { key: "meta_items", name: app.metaItemNameCaptial+'s' },
                { key: "meta_groups", name: app.metaItemNameCaptial+' Groups' }
            ]) :
            basic
    })
    const chosenOptions = ref([])
    const chosen = computed(() => chosenOptions.value.filter(d => d.chosen))

    const data = reactive({
        users: [],
        items: [],
        codes: [],
        tags: [],
        datatags: [],
        evidence: [],
        meta_items: [],
        meta_groups: [],
    })

    const exportImages = ref(true)

    const status = ref("")
    const filesToDo = ref(0)
    const filesDone = ref(0)
    const filesProcessed = computed(() => filesToDo.value <= 0 ? -1 : Math.round(filesDone.value / filesToDo.value * 100))

    const BATCH_SIZE = 50

    async function addFiles(folder, files, getUrl, checkDuplicates=false) {
        const done = new Set()
        const numBatches = Math.ceil(files.length / BATCH_SIZE)
        filesToDo.value = files.length
        filesDone.value = 0
        for (let i = 0; i < numBatches; ++i) {
            const start = i * BATCH_SIZE
            const end = Math.min((i+1) * BATCH_SIZE, files.length)
            await Promise.all(
                files.slice(start, end)
                .map(async name => {
                    if (checkDuplicates && done.has(name)) return
                    try {
                        const response = await axios.get(getUrl(name), { responseType: "arraybuffer" })
                        filesDone.value++
                        return folder.file(name, response.data, { binary: true })
                    } catch {
                        console.debug("failed to load file", name)
                    }
                    filesDone.value++
                    return null
                })
            )
        }
        filesToDo.value = 0
    }

    async function exportData() {
        isLoading.value = true
        const zip = new JSZip()
        const csv = d3.dsvFormat(delim.value)

        status.value = "starting file preparation"

        await Promise.all(chosen.value.map(async (d) => {
            if (data[d.key].length === 0) return
            status.value = "preparing " + d.key + ".csv file"
            zip.file(d.key+".csv", csv.format(data[d.key]))
            if (exportImages.value) {
                // add folder for item teasers
                if (d.key === "items") {
                    const folder = zip.folder("teaser")
                    const names = data.items.map(item => item.teaser).filter(img => img)
                    await addFiles(folder, names, n => mediaPath("teaser", n))
                }
                // add folder for evidence media
                else if (d.key === "evidence") {
                    const folder = zip.folder("evidence")
                    const names = data.evidence.map(e => e.filepath).filter(img => img)
                    return await addFiles(folder, names, n => mediaPath("evidence", n), true)
                }
            }
        }))

        status.value = "generating .zip file"

        zip.generateAsync({type:"blob"}).then(blob => {
            status.value = "done"
            isLoading.value = false
            saveAs(blob, filename.value.endsWith(".zip") ? filename.value : filename.value+".zip")
            status.value = ""
        })
    }

    async function readData() {
        if (!ds.value) return
        data.users = await api.loadUsersByDataset(ds.value);
        data.items = await api.loadItemsByDataset(ds.value)
        if (activeCode.value) {
            readCodeData()
        } else {
            data.codes = await api.loadCodesByDataset(ds.value)
            data.tags = await api.loadTagsByDataset(ds.value)
            data.datatags = await api.loadDataTagsByDataset(ds.value)
            data.evidence = await api.loadEvidenceByDataset(ds.value)
            if (app.hasMetaItems) {
                data.meta_groups = await api.loadExtGroupsByDataset(ds.value)
                const conns = await api.loadExtConnectionsByDataset(ds.value)
                const mi = await api.loadExternalizationsByDataset(ds.value)
                mi.forEach(d => {
                    d.categories = conns[0].filter(c => c.meta_id === d.id).map(d => d.cat_id)
                    d.tags = conns[1].filter(t => t.meta_id === d.id).map(d => d.tag_id)
                    d.evidence = conns[2].filter(t => t.meta_id === d.id).map(d => d.ev_id)
                });
                data.meta_items = mi
            } else {
                data.meta_groups = []
                data.meta_items = []
            }
        }
    }
    async function readCodeData() {
        if (!activeCode.value) return
        data.tags = await api.loadTagsByCode(activeCode.value)
        data.datatags = await api.loadDataTagsByCode(activeCode.value)
        data.evidence = await api.loadEvidenceByCode(activeCode.value)
        if (app.hasMetaItems) {
            data.meta_groups = await api.loadExtGroupsByCode(activeCode.value)
            const conns = await api.loadExtConnectionsByCode(activeCode.value)
            const mi = await api.loadExternalizationsByCode(activeCode.value)
            mi.forEach(d => {
                d.categories = conns[0].filter(c => c.meta_id === d.id).map(d => d.cat_id)
                d.tags = conns[1].filter(t => t.meta_id === d.id).map(d => d.tag_id)
                d.evidence = conns[2].filter(t => t.meta_id === d.id).map(d => d.ev_id)
            });
            data.meta_items = mi
        } else {
            data.meta_groups = []
            data.meta_items = []
        }
    }

    async function readOnCode() {
        const obj = chosenOptions.value.find(d => d.key === "codes")
        obj.chosen = false
        readCodeData()
    }

    async function readOnDataset() {
        if (!ds.value) {
            codes.value = []
            chosenOptions.value = []
        } else {
            codes.value = await api.loadCodesByDataset(ds.value)
            chosenOptions.value = dataOptions.value.map(d => {
                const obj = Object.assign({}, d)
                obj.chosen = obj.key !== "users" && obj.key !== "codes"
                return obj
            })
            readData()
        }
    }

    onMounted(readOnDataset)

    watch(ds, readOnDataset)
    watch(activeCode, readOnCode)

</script>