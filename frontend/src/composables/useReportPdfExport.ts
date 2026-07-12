async function loadPdfDeps() {
  const [html2canvasMod, jspdfMod] = await Promise.all([
    import('html2canvas'),
    import('jspdf'),
  ])
  return {
    html2canvas: html2canvasMod.default,
    jsPDF: jspdfMod.jsPDF,
  }
}

async function captureElement(canvasLib: typeof import('html2canvas').default, node: HTMLElement) {
  return canvasLib(node, {
    scale: 2,
    useCORS: true,
    logging: false,
    backgroundColor: '#ffffff',
  })
}

function appendCanvasToPdf(
  pdf: InstanceType<typeof import('jspdf').jsPDF>,
  canvas: HTMLCanvasElement,
  pageWidth: number,
  pageHeight: number,
) {
  const imgData = canvas.toDataURL('image/jpeg', 0.92)
  const imgWidth = pageWidth
  const imgHeight = (canvas.height * imgWidth) / canvas.width

  let heightLeft = imgHeight
  let position = 0

  pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
  heightLeft -= pageHeight

  while (heightLeft > 0) {
    position = heightLeft - imgHeight
    pdf.addPage()
    pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight
  }
}

/** 按章节分页导出，避免单张长图拉伸模糊 */
export async function exportReportElementToPdf(
  element: HTMLElement,
  filename: string,
): Promise<void> {
  const { html2canvas, jsPDF } = await loadPdfDeps()
  element.classList.add('report-body--export')

  try {
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const chapters = Array.from(element.querySelectorAll<HTMLElement>('.report-chapter'))

    if (!chapters.length) {
      const canvas = await captureElement(html2canvas, element)
      appendCanvasToPdf(pdf, canvas, pageWidth, pageHeight)
      pdf.save(filename)
      return
    }

    for (let i = 0; i < chapters.length; i += 1) {
      const chapter = chapters[i]
      const canvas = await captureElement(html2canvas, chapter)
      if (i > 0) pdf.addPage()
      const imgData = canvas.toDataURL('image/jpeg', 0.92)
      const imgWidth = pageWidth
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      const offsetY = imgHeight > pageHeight ? 0 : (pageHeight - imgHeight) / 2
      pdf.addImage(imgData, 'JPEG', 0, offsetY, imgWidth, Math.min(imgHeight, pageHeight))
    }

    pdf.save(filename)
  } finally {
    element.classList.remove('report-body--export')
  }
}
