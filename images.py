import os
from PIL import Image, ImageCms
import csv
from io import BytesIO
import concurrent.futures

def get_icc_profile_description(icc_profile):
    try:
        profile = ImageCms.ImageCmsProfile(BytesIO(icc_profile))
        return profile.profile_description
    except Exception:
        return "Unknown"

def process_image(filepath, root_dir, lossy_qualities, methods, alpha_qualities):
    try:
        original_size = os.path.getsize(filepath)
        relative_path = os.path.relpath(filepath, root_dir)
        file_type = os.path.splitext(filepath)[1].lstrip('.').upper()

        try:
            img = Image.open(filepath)
            width, height = img.size
            scale = f"{width}x{height}"
            has_alpha = img.mode in ('RGBA', 'LA', 'P')
            icc_profile = img.info.get('icc_profile')
            icc_profile_description = get_icc_profile_description(icc_profile) if icc_profile else "None"
        except Exception:
            return [relative_path, original_size, "N/A", False, file_type, "N/A", "N/A", "N/A"]

        row = [relative_path, original_size, scale, has_alpha, file_type, icc_profile_description]

        # Lossless WebP
        buffer = BytesIO()
        img.save(buffer, "webp", lossless=True, exact=True, icc_profile=icc_profile)
        row.append(buffer.tell())

        # Lossless WebP no alpha
        if has_alpha:
            img_no_alpha = img.convert("RGB")
            buffer = BytesIO()
            img_no_alpha.save(buffer, "webp", lossless=True, exact=True, icc_profile=icc_profile)
            row.append(buffer.tell())
        else:
            row.append("N/A")

        # Lossy WebP with different settings
        for quality in lossy_qualities:
            for method in methods:
                # Lossy with alpha
                if has_alpha:
                    for alpha_quality in alpha_qualities:
                        buffer = BytesIO()
                        img.save(buffer, "webp", quality=quality, method=method, alpha_quality=alpha_quality, exact=True, icc_profile=icc_profile)
                        row.append(buffer.tell())
                else:
                    row.extend(["N/A"] * len(alpha_qualities))
                # Lossy no alpha
                buffer = BytesIO()
                if has_alpha:
                    img_no_alpha = img.convert("RGB")
                    img_no_alpha.save(buffer, "webp", quality=quality, method=method, exact=True, icc_profile=icc_profile)
                else:
                    img.save(buffer, "webp", quality=quality, method=method, exact=True, icc_profile=icc_profile)
                row.append(buffer.tell())

        return row

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def convert_images_to_webp_report(root_dir, lossy_qualities=[75, 50, 25], methods=[0, 4, 6], alpha_qualities=[100, 80], image_limit=10):
    report_data = []
    image_count = 0
    file_list = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.webp', '.gif')):
                file_list.append(os.path.join(root, file))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_image, filepath, root_dir, lossy_qualities, methods, alpha_qualities) for filepath in file_list]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                report_data.append(result)
                image_count += 1
                if image_count == image_limit:
                    break

    with open("webp_compression_report.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        header = ["Relative Path", "Original Size", "Scale", "Has Alpha", "File Type", "ICC Profile", "Lossless Size", "Lossless No Alpha Size"]
        for quality in lossy_qualities:
            for method in methods:
                if report_data and report_data and report_data[0][3]:
                    for alpha_quality in alpha_qualities:
                        header.append(f"lossy_q{quality}_m{method}_a{alpha_quality}")
                header.append(f"lossy_q{quality}_m{method}_no_alpha")
        writer.writerow(header)
        writer.writerows(report_data)

if __name__ == "__main__":
    current_directory = os.getcwd()
    lossy_qualities = [75, 50, 25]
    methods = [0, 4, 6]
    alpha_qualities = [100, 80]
    image_limit = 10000
    convert_images_to_webp_report(current_directory, lossy_qualities, methods, alpha_qualities, image_limit)
    print("Report generated: webp_compression_report.csv")