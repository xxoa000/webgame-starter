/* 기관 네 곳의 편제와 역할을 표시한다. */
import styles from "../home/Home.module.css";
import { classNames } from "../../lib/classNames";
import { DEPARTMENTS } from "../../lib/world";
const departmentStyles: Record<string, string> = {
  control: "",
  field: styles.field,
  research: styles.research,
  hazard: styles.hazard,
};
export function DepartmentDirectory() {
  /* 기관 네 곳의 편제와 역할을 표시한다. */

  return (
    <section
      className={styles.departmentDirectory}
      aria-label="기관 구성"
    >
      <div className={styles.directoryTitle}>
        <span>기관 편제</span>
        <small>ORGANIZATION / 04</small>
      </div>
      <div className={styles.departmentGrid}>
        {DEPARTMENTS.map((department) => {
          return (
            <article
              className={classNames(
                styles.department,
                departmentStyles[department.tone],
              )}
              key={department.id}
            >
              <span className={styles.departmentNumber}>{department.id}</span>
              <div>
                <h3>{department.name}</h3>
                <small>{department.role}</small>
                <p>{department.description}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
