<template>
    <div>
        <h4 v-if="label">{{ label }}</h4>
        <v-sheet rounded color="surface-light" class="pa-2 d-flex">
            <div>
                <v-sheet
                    rounded
                    color="surface-brighter"
                    class="pa-2 mb-1 d-flex align-center justify-center"
                    @dragover.prevent
                    @drop.prevent="e => onDrop(e, true)"
                    :style="{ minHeight: ((height+15)*2)+'px' }"
                    style="min-width: 300px">
                    <b>Drop images to replace</b>
                </v-sheet>
                <v-sheet
                    rounded
                    color="surface-brighter"
                    class="pa-2 d-flex align-center justify-center"
                    @dragover.prevent
                    @drop.prevent="e => onDrop(e, false)"
                    :style="{ minHeight: ((height+15)*2)+'px' }"
                    style="min-width: 300px">
                    <b>Drop images to add</b>
                </v-sheet>
            </div>
            <div v-if="numImages > 0" class="d-flex flex-wrap align-content-start align-start ml-2" :style="{ maxHeight: ((height+15)*4)+'px', overflowY: 'auto' }">
                <v-img v-for="i in Math.min(numImages, maxDisplay)"
                    cover
                    class="ma-1"
                    :src="images[i-1]"
                    :lazy-src="imgUrlS"
                    :style="{ maxWidth: width+'px', maxHeight: height+'px' }"
                    :width="width"
                    :height="height"/>
                <span v-if="numImages > maxDisplay" class="ma-1">and {{ numImages-maxDisplay }} more..</span>
            </div>
        </v-sheet>
        <v-overlay
            :model-value="isLoading"
            opacity="0.75"
            class="align-center justify-center flex-wrap">
            <v-progress-linear :model-value="(numImages-numStart) / (target-numStart) * 100" size="256" color="primary"></v-progress-linear>
            <div>loaded {{ numImages-numStart }} our of {{ target-numStart }} images</div>
        </v-overlay>
    </div>
</template>

<script setup>
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { computed } from 'vue'
    import { useToast } from 'vue-toastification'

    const toast = useToast()

    const props = defineProps({
        label: {
            type: String,
            required: false
        },
        width: {
            type: Number,
            default: 160
        },
        height: {
            type: Number,
            default: 80
        },
        maxDisplay: {
            type: Number,
            default: 200
        }
    })

    const emit = defineEmits(["change"])

    const numImages = ref(0)
    const target = ref(0)
    const numStart = ref(0)
    const isLoading = computed(() => target.value > numImages.value)

    let images = [], imageFiles = []

    function onLoad(files, replace=true) {
        if (replace) {
            numImages.value = 0
            images = []
        }
        numStart.value = images.length
        target.value = images.length + files.length

        files.forEach(file => {
            const reader = new FileReader();
            imageFiles.push(file)
            reader.addEventListener('load', () => {
                images.push(reader.result)
                numImages.value++
                if (numImages.value === target.value) {
                    emit("change", imageFiles)
                }
            })
            reader.readAsDataURL(file);
        });
    }

    function onDrop(ev, replace=true) {
        const files = []

        if (isLoading.value) {
            return toast.error("still uploading images..")
        }

        if (ev.dataTransfer.items) {
            // Use DataTransferItemList interface to access the file(s)
            [...ev.dataTransfer.items].forEach((item, i) => {
                // If dropped items aren't files, reject them
                if (item.kind === "file") {
                    const file = item.getAsFile();
                    files.push(file)
                }
            });
        } else {
            // Use DataTransfer interface to access the file(s)
            [...ev.dataTransfer.files].forEach(file => files.push(file));
        }

        onLoad(files, replace)
    }

</script>